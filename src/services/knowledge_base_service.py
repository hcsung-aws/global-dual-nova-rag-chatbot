"""
Knowledge Base 서비스 모듈

Bedrock Knowledge Base를 사용한 문서 검색 서비스를 제공합니다.
기존 search_knowledge_base() 함수를 클래스 기반으로 리팩토링했습니다.
"""

import re
from typing import List, Dict, Any, Optional


class KnowledgeBaseService:
    """Bedrock Knowledge Base 검색 서비스 클래스
    
    벡터 검색을 통해 관련 문서를 찾고 구조화된 결과를 반환합니다.
    """
    
    def __init__(self, aws_client_manager, knowledge_base_id: str = 'SJJP9YYPHX', logger=None):
        """Knowledge Base 서비스 초기화
        
        Args:
            aws_client_manager: AWS 클라이언트 관리자 인스턴스
            knowledge_base_id: Knowledge Base ID
            logger: 로깅 인스턴스 (선택사항)
        """
        self.aws_manager = aws_client_manager
        self.knowledge_base_id = knowledge_base_id
        self.logger = logger
        self.bedrock_agent_client = None
        
    def _get_bedrock_agent_client(self):
        """Bedrock Agent Runtime 클라이언트 지연 로딩"""
        if not self.bedrock_agent_client:
            self.bedrock_agent_client = self.aws_manager.get_client(
                'bedrock-agent-runtime', 
                region_name='us-east-1'
            )
        return self.bedrock_agent_client
    
    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출 - 개선된 버전
        
        Args:
            query: 검색 쿼리
            
        Returns:
            List[str]: 추출된 키워드 목록
        """
        # 불용어 제거
        stop_words = {
            '에', '대해', '대해서', '에서', '를', '을', '가', '이', '은', '는', '의', 
            '와', '과', '로', '으로', '에게', '한테', '께', '부터', '까지', 
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
            'for', 'of', 'with', 'by', 'about', 'how', 'what', 'when', 
            'where', 'why', 'who', 'me', 'tell', 'is', 'are', 'was', 'were'
        }
        
        # 조사 제거를 위한 패턴
        query_cleaned = re.sub(
            r'(에서|에게|에|를|을|가|이|은|는|의|와|과|로|으로|한테|께|부터|까지)(?=\s|$)', 
            '', 
            query
        )
        
        # 특수문자 제거 및 단어 분리
        words = re.findall(r'\b\w+\b', query_cleaned.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 추가로 원본 쿼리에서도 키워드 추출
        original_words = re.findall(r'\b\w+\b', query.lower())
        for word in original_words:
            if word not in stop_words and len(word) > 1 and word not in keywords:
                keywords.append(word)
        
        return list(set(keywords))  # 중복 제거
    
    def _extract_title_from_s3_uri(self, s3_uri: str) -> str:
        """S3 URI에서 문서 제목 추출
        
        Args:
            s3_uri: S3 URI
            
        Returns:
            str: 추출된 제목
        """
        if not s3_uri:
            return "Knowledge Base Document"
        
        try:
            # S3 URI에서 파일명 추출하여 제목으로 사용
            filename = s3_uri.split('/')[-1]
            title = filename.replace('.json', '').replace('.txt', '').replace('_', ' ')
            return title if title else "Knowledge Base Document"
        except Exception:
            return "Knowledge Base Document"
    
    def search_knowledge_base(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Bedrock Knowledge Base에서 문서 검색
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
                - title: 문서 제목
                - content: 문서 내용
                - url: 문서 URL (S3 URI)
                - score: 관련성 점수
                - matched_keywords: 매칭된 키워드 (빈 리스트, 벡터 검색이므로)
        """
        try:
            bedrock_agent_client = self._get_bedrock_agent_client()
            
            response = bedrock_agent_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = []
            for result in response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                score = result.get('score', 0)
                location = result.get('location', {})
                
                # S3 location에서 제목 추출 시도
                s3_uri = location.get('s3Location', {}).get('uri', '')
                title = self._extract_title_from_s3_uri(s3_uri)
                
                results.append({
                    'title': title,
                    'content': content,
                    'url': s3_uri if s3_uri else '#',
                    'score': score,
                    'matched_keywords': []  # Knowledge Base는 벡터 검색으로 관련성 자동 계산
                })
            
            # 로깅
            if self.logger:
                self.logger.log_request(f"Knowledge Base 검색: {query}", len(results))
            
            print(f"=== Knowledge Base 검색 결과 ===")
            print(f"쿼리: {query}")
            print(f"결과 수: {len(results)}")
            for i, result in enumerate(results[:3]):  # 상위 3개만 로그
                print(f"{i+1}. {result['title']} (점수: {result['score']:.3f})")
            print("=" * 35)
            
            return results
            
        except Exception as e:
            error_msg = f"Knowledge Base 검색 중 오류: {e}"
            print(error_msg)
            if self.logger:
                self.logger.log_error(error_msg)
            
            return []
    
    def search_with_keywords(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """키워드 추출과 함께 Knowledge Base 검색
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 (키워드 정보 포함)
        """
        # 키워드 추출
        keywords = self._extract_keywords(query)
        
        # Knowledge Base 검색
        results = self.search_knowledge_base(query, max_results)
        
        # 결과에 키워드 정보 추가 (참고용)
        for result in results:
            result['extracted_keywords'] = keywords
        
        return results
    
    def get_document_by_title(self, title: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """문서 제목으로 검색
        
        Args:
            title: 문서 제목
            max_results: 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        return self.search_knowledge_base(title, max_results)
    
    def search_by_content_type(self, query: str, content_filter: str = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """콘텐츠 유형별 검색 (확장 가능한 메서드)
        
        Args:
            query: 검색 쿼리
            content_filter: 콘텐츠 필터 (향후 확장용)
            max_results: 최대 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        results = self.search_knowledge_base(query, max_results)
        
        # 향후 콘텐츠 필터링 로직 추가 가능
        if content_filter:
            # 예: 특정 유형의 문서만 필터링
            filtered_results = []
            for result in results:
                if content_filter.lower() in result['title'].lower() or content_filter.lower() in result['content'].lower():
                    filtered_results.append(result)
            return filtered_results
        
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """Knowledge Base 연결 상태 확인
        
        Returns:
            Dict[str, Any]: 상태 정보
                - status: 연결 상태 ("healthy" 또는 "error")
                - knowledge_base_id: Knowledge Base ID
                - test_query_results: 테스트 쿼리 결과 수
                - error: 오류 메시지 (오류 시)
        """
        try:
            # 직접 Bedrock Agent 클라이언트를 호출하여 상태 확인
            bedrock_agent_client = self._get_bedrock_agent_client()
            
            response = bedrock_agent_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': 'test'},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 1
                    }
                }
            )
            
            test_results_count = len(response.get('retrievalResults', []))
            
            return {
                'status': 'healthy',
                'knowledge_base_id': self.knowledge_base_id,
                'test_query_results': test_results_count,
                'client_available': self.bedrock_agent_client is not None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'knowledge_base_id': self.knowledge_base_id,
                'error': str(e),
                'client_available': False
            }