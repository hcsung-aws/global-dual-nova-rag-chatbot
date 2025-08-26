#!/usr/bin/env python3
"""
마이그레이션 검증 종합 실행 스크립트

이 스크립트는 코드 최적화 및 중복 제거 마이그레이션의 모든 검증 테스트를 실행하고
종합적인 보고서를 생성합니다.
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MigrationVerificationRunner:
    """마이그레이션 검증 실행기"""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'performance_metrics': {}
        }
    
    def run_test_suite(self, test_file: str, description: str) -> bool:
        """테스트 스위트 실행"""
        print(f"\n{'='*60}")
        print(f"실행 중: {description}")
        print(f"파일: {test_file}")
        print(f"{'='*60}")
        
        try:
            # pytest 실행
            cmd = [
                sys.executable, '-m', 'pytest', 
                test_file, 
                '-v', '--tb=short', '--no-header'
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd, 
                cwd=self.project_root,
                capture_output=True, 
                text=True, 
                timeout=300  # 5분 타임아웃
            )
            end_time = time.time()
            
            # 결과 저장
            self.results['tests'][test_file] = {
                'description': description,
                'success': result.returncode == 0,
                'duration': end_time - start_time,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if result.returncode == 0:
                print(f"✅ {description} - 성공")
            else:
                print(f"❌ {description} - 실패")
                print(f"오류 출력:\n{result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - 타임아웃")
            self.results['tests'][test_file] = {
                'description': description,
                'success': False,
                'duration': 300,
                'error': 'Timeout'
            }
            return False
        except Exception as e:
            print(f"💥 {description} - 예외 발생: {e}")
            self.results['tests'][test_file] = {
                'description': description,
                'success': False,
                'duration': 0,
                'error': str(e)
            }
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 마이그레이션 검증 테스트 시작")
        print(f"프로젝트 루트: {self.project_root}")
        
        # 테스트 스위트 목록
        test_suites = [
            ('tests/test_aws_clients.py', 'AWS 클라이언트 관리자 단위 테스트'),
            ('tests/test_glossary_manager.py', '게임 용어 단어장 관리자 단위 테스트'),
            ('tests/test_config_manager.py', '설정 관리자 단위 테스트'),
            ('tests/test_translation_service.py', '번역 서비스 단위 테스트'),
            ('tests/test_bedrock_service.py', 'Bedrock 서비스 단위 테스트'),
            ('tests/test_knowledge_base_service.py', '지식베이스 서비스 단위 테스트'),
            ('tests/test_streaming_handler.py', '스트리밍 핸들러 단위 테스트'),
            ('tests/test_dual_response.py', '이중 언어 응답 생성 단위 테스트'),
            ('tests/test_system_integration.py', '시스템 통합 테스트'),
            ('tests/test_performance_benchmarks.py', '성능 벤치마크 테스트'),
            ('tests/test_migration_verification.py', '마이그레이션 검증 테스트'),
        ]
        
        # 각 테스트 스위트 실행
        total_tests = len(test_suites)
        passed_tests = 0
        
        for test_file, description in test_suites:
            if self.run_test_suite(test_file, description):
                passed_tests += 1
        
        # 결과 요약
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100
        }
        
        return passed_tests == total_tests
    
    def load_performance_metrics(self):
        """성능 메트릭 로드"""
        metrics_file = self.project_root / 'migration_performance_report.json'
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    self.results['performance_metrics'] = json.load(f)
            except Exception as e:
                print(f"성능 메트릭 로드 실패: {e}")
    
    def generate_report(self):
        """종합 보고서 생성"""
        self.load_performance_metrics()
        
        print(f"\n{'='*80}")
        print("마이그레이션 검증 종합 보고서")
        print(f"{'='*80}")
        print(f"실행 시간: {self.results['timestamp']}")
        print(f"총 테스트 스위트: {self.results['summary']['total_tests']}")
        print(f"성공한 테스트: {self.results['summary']['passed_tests']}")
        print(f"실패한 테스트: {self.results['summary']['failed_tests']}")
        print(f"성공률: {self.results['summary']['success_rate']:.1f}%")
        
        # 개별 테스트 결과
        print(f"\n{'='*60}")
        print("개별 테스트 결과")
        print(f"{'='*60}")
        
        for test_file, result in self.results['tests'].items():
            status = "✅ 성공" if result['success'] else "❌ 실패"
            duration = result.get('duration', 0)
            print(f"{status} | {duration:6.2f}초 | {result['description']}")
        
        # 성능 메트릭
        if self.results['performance_metrics']:
            print(f"\n{'='*60}")
            print("성능 메트릭")
            print(f"{'='*60}")
            
            before = self.results['performance_metrics'].get('before_migration', {})
            after = self.results['performance_metrics'].get('after_migration', {})
            
            for metric in after:
                if metric in before:
                    before_val = before[metric]
                    after_val = after[metric]
                    if before_val > 0:
                        improvement = ((before_val - after_val) / before_val) * 100
                        print(f"{metric}: {improvement:+.1f}% 개선")
        
        # 보고서 파일 저장
        report_file = self.project_root / 'migration_verification_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 상세 보고서가 {report_file}에 저장되었습니다.")
        
        # 최종 결과
        if self.results['summary']['success_rate'] == 100:
            print(f"\n🎉 모든 마이그레이션 검증 테스트가 성공했습니다!")
            return True
        else:
            print(f"\n⚠️  일부 테스트가 실패했습니다. 상세 내용을 확인해주세요.")
            return False
    
    def check_environment(self):
        """환경 검사"""
        print("🔍 환경 검사 중...")
        
        # Python 버전 확인
        python_version = sys.version_info
        print(f"Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 필수 디렉토리 확인
        required_dirs = ['src', 'tests', 'config', 'logs']
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                print(f"✅ {dir_name} 디렉토리 존재")
            else:
                print(f"❌ {dir_name} 디렉토리 없음")
                return False
        
        # logs 디렉토리 생성 (없는 경우)
        logs_dir = self.project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        return True


def main():
    """메인 함수"""
    runner = MigrationVerificationRunner()
    
    # 환경 검사
    if not runner.check_environment():
        print("❌ 환경 검사 실패")
        sys.exit(1)
    
    # 모든 테스트 실행
    success = runner.run_all_tests()
    
    # 보고서 생성
    report_success = runner.generate_report()
    
    # 최종 결과
    if success and report_success:
        print("\n🎯 마이그레이션 검증이 성공적으로 완료되었습니다!")
        sys.exit(0)
    else:
        print("\n💥 마이그레이션 검증 중 문제가 발생했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()