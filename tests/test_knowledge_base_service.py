"""
KnowledgeBaseService 단위 테스트

Knowledge Base 검색 서비스의 핵심 기능을 검증합니다.
"""

import pytest
from unittest.mock import Mock, patch
from src.services.knowledge_base_service import KnowledgeBaseService


class TestKnowledgeBaseService:
    """KnowledgeBaseService 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.mock_aws_manager = Mock()
        self.mock_bedrock_agent_client = Mock()
        self.mock_aws_manager.get_client.return_value = self.mock_bedrock_agent_client
        
        self.kb_service = KnowledgeBaseService(
            self.mock_aws_manager, 
            knowledge_base_id='TEST_KB_ID'
        )
    
    def test_extract_keywords_korean(self):
        """한국어 키워드 추출 테스트"""
        query = "아마존 생존기에 대해서 알려주세요"
        keywords = self.kb_service._extract_keywords(query)
        
        # 불용어가 제거되고 의미있는 키워드만 추출되는지 확인
        assert "아마존" in keywords
        assert "생존기" in keywords
        assert "대해서" not in keywords  # 불용어 제거 확인
        assert "에" not in keywords  # 불용어 제거 확인
    
    def test_extract_keywords_english(self):
        """영어 키워드 추출 테스트"""
        query = "Tell me about Amazon Survival game"
        keywords = self.kb_service._extract_keywords(query)
        
        assert "amazon" in keywords
        assert "survival" in keywords
        assert "game" in keywords
        assert "about" not in keywords  # 불용어 제거 확인
        assert "me" not in keywords  # 불용어 제거 확인
    
    def test_extract_keywords_mixed_language(self):
        """한영 혼합 키워드 추출 테스트"""
        query = "Amazon 생존기 게임에 대해 알려주세요"
        keywords = self.kb_service._extract_keywords(query)
        
        assert "amazon" in keywords
        assert "생존기" in keywords
        assert "게임" in keywords
    
    def test_extract_title_from_s3_uri(self):
        """S3 URI에서 제목 추출 테스트"""
        # 정상적인 S3 URI
        s3_uri = "s3://bucket/path/amazon_survival_guide.json"
        title = self.kb_service._extract_title_from_s3_uri(s3_uri)
        assert title == "amazon survival guide"
        
        # 확장자가 다른 경우
        s3_uri = "s3://bucket/cs_response_format.txt"
        title = self.kb_service._extract_title_from_s3_uri(s3_uri)
        assert title == "cs response format"
        
        # 빈 URI
        title = self.kb_service._extract_title_from_s3_uri("")
        assert title == "Knowledge Base Document"
        
        # None URI
        title = self.kb_service._extract_title_from_s3_uri(None)
        assert title == "Knowledge Base Document"
    
    def test_search_knowledge_base_success(self):
        """Knowledge Base 검색 성공 테스트"""
        # Mock 응답 설정
        mock_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Amazon Survival Game Guide'},
                    'score': 0.95,
                    'location': {
                        's3Location': {
                            'uri': 's3://bucket/amazon_survival.json'
                        }
                    }
                },
                {
                    'content': {'text': 'Character Information'},
                    'score': 0.85,
                    'location': {
                        's3Location': {
                            'uri': 's3://bucket/characters.json'
                        }
                    }
                }
            ]
        }
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행
        results = self.kb_service.search_knowledge_base("Amazon Survival", max_results=5)
        
        # 검증
        assert len(results) == 2
        assert results[0]['title'] == 'amazon survival'
        assert results[0]['content'] == 'Amazon Survival Game Guide'
        assert results[0]['score'] == 0.95
        assert results[0]['url'] == 's3://bucket/amazon_survival.json'
        assert results[0]['matched_keywords'] == []
        
        assert results[1]['title'] == 'characters'
        assert results[1]['content'] == 'Character Information'
        assert results[1]['score'] == 0.85
        
        # Bedrock Agent 클라이언트 호출 검증
        self.mock_bedrock_agent_client.retrieve.assert_called_once_with(
            knowledgeBaseId='TEST_KB_ID',
            retrievalQuery={'text': 'Amazon Survival'},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
    
    def test_search_knowledge_base_empty_results(self):
        """Knowledge Base 검색 결과 없음 테스트"""
        # 빈 응답 설정
        mock_response = {'retrievalResults': []}
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행
        results = self.kb_service.search_knowledge_base("nonexistent query")
        
        # 검증
        assert len(results) == 0
    
    def test_search_knowledge_base_error_handling(self):
        """Knowledge Base 검색 오류 처리 테스트"""
        # Bedrock Agent 클라이언트에서 예외 발생 시뮬레이션
        self.mock_bedrock_agent_client.retrieve.side_effect = Exception("API Error")
        
        # 테스트 실행
        results = self.kb_service.search_knowledge_base("test query")
        
        # 오류 시 빈 리스트 반환 검증
        assert results == []
    
    def test_search_with_keywords(self):
        """키워드와 함께 검색 테스트"""
        # Mock 응답 설정
        mock_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Test content'},
                    'score': 0.9,
                    'location': {'s3Location': {'uri': 's3://bucket/test.json'}}
                }
            ]
        }
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행
        results = self.kb_service.search_with_keywords("아마존 생존기에 대해 알려주세요")
        
        # 검증
        assert len(results) == 1
        assert 'extracted_keywords' in results[0]
        assert "아마존" in results[0]['extracted_keywords']
        assert "생존기" in results[0]['extracted_keywords']
    
    def test_get_document_by_title(self):
        """제목으로 문서 검색 테스트"""
        # Mock 응답 설정
        mock_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Document content'},
                    'score': 0.95,
                    'location': {'s3Location': {'uri': 's3://bucket/doc.json'}}
                }
            ]
        }
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행
        results = self.kb_service.get_document_by_title("Amazon Survival Guide")
        
        # 검증
        assert len(results) == 1
        assert results[0]['content'] == 'Document content'
        
        # 올바른 파라미터로 호출되었는지 확인
        self.mock_bedrock_agent_client.retrieve.assert_called_once_with(
            knowledgeBaseId='TEST_KB_ID',
            retrievalQuery={'text': 'Amazon Survival Guide'},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3
                }
            }
        )
    
    def test_search_by_content_type_no_filter(self):
        """콘텐츠 유형별 검색 (필터 없음) 테스트"""
        # Mock 응답 설정
        mock_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Test content'},
                    'score': 0.9,
                    'location': {'s3Location': {'uri': 's3://bucket/test.json'}}
                }
            ]
        }
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행 (필터 없음)
        results = self.kb_service.search_by_content_type("test query")
        
        # 검증
        assert len(results) == 1
        assert results[0]['content'] == 'Test content'
    
    def test_search_by_content_type_with_filter(self):
        """콘텐츠 유형별 검색 (필터 있음) 테스트"""
        # Mock 응답 설정
        mock_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Amazon survival guide content'},
                    'score': 0.9,
                    'location': {'s3Location': {'uri': 's3://bucket/amazon_guide.json'}}
                },
                {
                    'content': {'text': 'Other game content'},
                    'score': 0.8,
                    'location': {'s3Location': {'uri': 's3://bucket/other.json'}}
                }
            ]
        }
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행 (Amazon 필터)
        results = self.kb_service.search_by_content_type("game", content_filter="amazon")
        
        # 검증 - Amazon이 포함된 결과만 반환되어야 함
        assert len(results) == 1
        assert "amazon" in results[0]['content'].lower()
    
    def test_health_check_success(self):
        """Health check 성공 테스트"""
        # Mock 응답 설정
        mock_response = {
            'retrievalResults': [
                {
                    'content': {'text': 'Test'},
                    'score': 0.5,
                    'location': {'s3Location': {'uri': 's3://bucket/test.json'}}
                }
            ]
        }
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행
        health_status = self.kb_service.health_check()
        
        # 검증
        assert health_status['status'] == 'healthy'
        assert health_status['knowledge_base_id'] == 'TEST_KB_ID'
        assert health_status['test_query_results'] == 1
        assert 'client_available' in health_status
    
    def test_health_check_error(self):
        """Health check 오류 테스트"""
        # Bedrock Agent 클라이언트에서 예외 발생 시뮬레이션
        self.mock_bedrock_agent_client.retrieve.side_effect = Exception("Connection Error")
        
        # 테스트 실행
        health_status = self.kb_service.health_check()
        
        # 검증
        assert health_status['status'] == 'error'
        assert health_status['knowledge_base_id'] == 'TEST_KB_ID'
        assert 'error' in health_status
        assert health_status['client_available'] == False
    
    def test_logger_integration(self):
        """로거 통합 테스트"""
        mock_logger = Mock()
        kb_service_with_logger = KnowledgeBaseService(
            self.mock_aws_manager, 
            logger=mock_logger
        )
        
        # Mock 응답 설정
        mock_response = {'retrievalResults': []}
        self.mock_bedrock_agent_client.retrieve.return_value = mock_response
        
        # 테스트 실행
        kb_service_with_logger.search_knowledge_base("test query")
        
        # 로거 호출 검증
        mock_logger.log_request.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])