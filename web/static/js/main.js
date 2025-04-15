document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소 참조
    const searchInput = document.getElementById('search-input');
    const searchForm = document.getElementById('search-form');
    const docTypeSelect = document.getElementById('doc_type');
    const ministrySelect = document.getElementById('ministry');
    const sortBySelect = document.getElementById('sort-by');
    const searchResults = document.getElementById('templates-container');
    const initialMessage = document.getElementById('initial-message');
    const noResults = document.getElementById('no-results');
    const loading = document.getElementById('loading');
    const pagination = document.getElementById('pagination');
    const templateModal = document.getElementById('template-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    const closeModal = document.getElementById('close-modal');
    // const selectTemplate = document.getElementById('select-template'); // 사용되지 않는 요소 참조 주석 처리 또는 제거
    
    // 보고서 관련 DOM 요소 참조
    const generateReportBtn = document.getElementById('generate-report-btn');
    const reportModal = document.getElementById('report-modal');
    const closeReportModal = document.getElementById('close-report-modal');
    const cancelReport = document.getElementById('cancel-report');
    const generateReport = document.getElementById('generate-report');
    const reportInput = document.getElementById('report-input');
    const characterCount = document.getElementById('character-count');
    const clearSelectionsBtn = document.getElementById('clear-selections');
    const analyzeTemplates = document.getElementById('analyze-templates');
    
    // 상태 변수
    let currentPage = 1;
    let totalPages = 1;
    // let selectedTemplate = null; // template.js 에서만 사용되므로 여기서 제거
    
    // 테마 토글 초기화
    initializeThemeToggle();
    
    
    // 검색 폼 제출 이벤트
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const keyword = searchInput.value.trim();
        const docType = docTypeSelect.value;
        
        // 필수 입력 필드 검증
        if (!keyword) {
            alert('검색어를 입력해주세요.');
            searchInput.focus();
            return;
        }
        
        if (!docType) {
            alert('문서 유형을 선택해주세요.');
            docTypeSelect.focus();
            return;
        }
        
        // 보도자료인 경우 담당자 입력은 선택 사항입니다.
        // (필수 확인 로직 제거됨)
        
        // 검색 결과 초기화
        document.getElementById('templates-container').innerHTML = '';
        document.getElementById('search-summary').classList.add('hidden');
        document.getElementById('pagination').innerHTML = '';
        document.getElementById('pagination').classList.add('hidden');
        document.getElementById('no-results').classList.add('hidden');
        
        // 페이지 초기화 및 검색 실행 (약간의 지연으로 DOM 업데이트 보장)
        setTimeout(() => {
            fetchTemplates(1);
        }, 50);
    });
    
    // 템플릿 상세 모달 닫기 함수
    function closeTemplateModalWithAnimation() {
        templateModal.style.opacity = '0';
        setTimeout(() => {
            templateModal.classList.add('hidden');
            document.body.classList.remove('modal-open'); // 모달 닫을 때 body 스크롤 복원
        }, 300); // 애니메이션 시간과 일치
    }

    // 모달 닫기 버튼 클릭 이벤트
    closeModal.addEventListener('click', closeTemplateModalWithAnimation);

    // 외부 클릭 시 모달 닫기 이벤트
    templateModal.addEventListener('click', function(e) {
        if (e.target === templateModal) {
            closeTemplateModalWithAnimation();
        }
    });

    // 보고서 관련 이벤트
    
    // 모든 선택 취소 버튼
    clearSelectionsBtn.addEventListener('click', function() {
        selectedTemplates = [];
        
        // 모든 체크박스 초기화
        document.querySelectorAll('.template-checkbox').forEach(checkbox => {
            checkbox.checked = false;
            const customCheckbox = checkbox.nextElementSibling;
            const checkIcon = customCheckbox.querySelector('.fa-check');
            if (customCheckbox) customCheckbox.classList.remove('bg-primary', 'checked');
            if (checkIcon) checkIcon.classList.add('opacity-0');
            
            // 카드 선택 상태 제거
            const card = checkbox.closest('.template-card') || checkbox.closest('[data-template-id]');
            if (card) card.classList.remove('selected');
        });
        
        updateSelectedTemplatesUI();
    });
    
    // 보고서 생성 버튼 클릭 이벤트
    generateReportBtn.addEventListener('click', function() {
        // 입력 초기화
        reportInput.value = '';
        characterCount.textContent = '0/1000';
        
        // 모달 표시
        reportModal.style.opacity = '0';
        reportModal.classList.remove('hidden');
        document.body.classList.add('modal-open'); // 보고서 모달 열 때 body 스크롤 방지
        
        // 페이드 인 효과
        setTimeout(() => {
            reportModal.style.opacity = '1';
        }, 10);
    });
    
    // 보고서 입력 글자수 제한
    reportInput.addEventListener('input', function() {
        const currentLength = reportInput.value.length;
        characterCount.textContent = `${currentLength}/1000`;
        
        // 최대 글자수를 초과하면 입력 제한
        if (currentLength > 1000) {
            reportInput.value = reportInput.value.substring(0, 1000);
            characterCount.textContent = '1000/1000';
        }
    });
    
    // 보고서 모달 닫기 함수
    function closeReportModalWithAnimation() {
        reportModal.style.opacity = '0';
        setTimeout(() => {
            reportModal.classList.add('hidden');
            document.body.classList.remove('modal-open'); // 보고서 모달 닫을 때 body 스크롤 복원
            // 보고서 모달은 body 스크롤을 막지 않으므로 클래스 제거 불필요
        }, 300); // 애니메이션 시간과 일치
    }

    // 보고서 모달 닫기 이벤트 리스너 통합
    closeReportModal.addEventListener('click', closeReportModalWithAnimation);
    cancelReport.addEventListener('click', closeReportModalWithAnimation);
    reportModal.addEventListener('click', function(e) { // 외부 클릭
        if (e.target === reportModal) {
            closeReportModalWithAnimation();
        }
    });

    // 템플릿 분석 API 호출
    analyzeTemplates.addEventListener('click', async function() {
        if (selectedTemplates.length === 0) {
            alert('선택된 템플릿이 없습니다.');
            return;
        }
        
        // 로딩 상태 표시
        analyzeTemplates.disabled = true;
        analyzeTemplates.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>분석 중...';
        
        try {
            const templateIds = selectedTemplates.map(template => template.id);
            
            const response = await fetch('/api/drafts/analyze-templates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    template_ids: templateIds
                }),
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `API 요청 실패: ${response.status}`;
                
                try {
                    // 응답이 JSON인지 확인 후 오류 메시지 추출
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.error) {
                        errorMessage = errorJson.error;
                    }
                } catch (e) {
                    // JSON 파싱 실패 시 원본 텍스트 사용
                    if (errorText) {
                        errorMessage += ` - ${errorText}`;
                    }
                }
                
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            
            // 성공 메시지
            alert(`템플릿 분석 완료: ${result.template_count}개 템플릿이 ${result.output_file} 파일에 저장되었습니다.`);
            
            // NLP 분석 시작 확인
            if (confirm('수집된 템플릿 데이터를 자연어 처리(NLP) 기법으로 분석하시겠습니까?\n문서 구조, 어조, 핵심 키워드를 추출하고 결과는 JSON으로 저장됩니다.')) {
                // 템플릿 내용 분석 API 호출
                await analyzeTemplateContent(result.output_file);
            }
            
        } catch (error) {
            console.error('템플릿 분석 중 오류:', error);
            alert(`템플릿 분석 중 오류가 발생했습니다: ${error.message}`);
        } finally {
            // 버튼 상태 복원
            analyzeTemplates.disabled = false;
            analyzeTemplates.innerHTML = '템플릿 분석';
        }
    });
    
    // 템플릿 내용 분석 함수
    async function analyzeTemplateContent(jsonlFile) {
        try {
            // 분석 중 메시지 표시
            const loadingMessage = document.createElement('div');
            loadingMessage.className = 'fixed inset-0 bg-black/60 flex items-center justify-center z-50';
            loadingMessage.innerHTML = `
                <div class="bg-card rounded-lg shadow-lg p-6 max-w-md">
                    <div class="flex flex-col items-center">
                        <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mb-4"></div>
                        <p class="text-lg font-medium">템플릿 내용 분석 중...</p>
                        <p class="text-sm text-muted-foreground mt-2">문서 구조, 어조, 핵심 키워드를 추출하고 있습니다.</p>
                    </div>
                </div>
            `;
            document.body.appendChild(loadingMessage);
            
            const response = await fetch('/api/drafts/analyze-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonl_file: jsonlFile
                }),
            });
            
            // 로딩 메시지 제거
            document.body.removeChild(loadingMessage);
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `API 요청 실패: ${response.status}`;
                
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.error) {
                        errorMessage = errorJson.error;
                    }
                } catch (e) {
                    if (errorText) {
                        errorMessage += ` - ${errorText}`;
                    }
                }
                
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            
            // 성공 메시지
            alert(`템플릿 내용 분석 완료: 결과가 ${result.output_file} 파일에 저장되었습니다.`);
            
        } catch (error) {
            console.error('템플릿 내용 분석 중 오류:', error);
            alert(`템플릿 내용 분석 중 오류가 발생했습니다: ${error.message}`);
        }
    }

    // 생성된 보고서 결과 표시 함수
    function displayGeneratedReport(result) {
        // 결과 모달 생성
        const resultModal = document.createElement('div');
        resultModal.id = 'result-modal';
        resultModal.className = 'fixed inset-0 bg-black/80 flex items-center justify-center z-50 theme-transition';
        resultModal.style.opacity = '0';
        resultModal.style.transition = 'opacity 0.3s ease-in-out';
        
        // 모달 내용
        resultModal.innerHTML = `
            <div class="bg-card rounded-lg shadow-lg w-full max-w-4xl theme-transition relative p-6 max-h-[90vh] overflow-y-auto">
                <button id="close-result-modal" class="absolute top-4 right-4 text-muted-foreground hover:text-card-foreground transition-colors">
                    <i class="fas fa-times text-lg"></i>
                </button>
                <div>
                    <h2 class="text-2xl font-bold mb-2 text-card-foreground">생성된 보고서</h2>
                    <div class="flex justify-between items-center mb-4">
                        <p class="text-muted-foreground">AI가 생성한 문서입니다.</p>
                        <div class="flex items-center space-x-2">
                            <span class="text-sm text-muted-foreground">약 ${Math.ceil(result.token_info.output_tokens / 4)} 단어 (토큰: ${result.token_info.output_tokens})</span>
                            <button id="copy-result" class="btn btn-outline btn-sm"><i class="fas fa-copy mr-1"></i>복사</button>
                        </div>
                    </div>
                    
                    <div class="mb-4 border rounded-lg p-4 bg-muted/50 whitespace-pre-wrap theme-transition">
                        ${result.content.replace(/\n/g, '<br>')}
                    </div>
                    
                    <div class="border-t pt-4 mt-4">
                        <div class="flex justify-between items-center mb-2">
                            <h3 class="font-medium">토큰 사용 정보</h3>
                            <span class="text-sm text-muted-foreground">추정 비용: ${result.token_info.cost_krw.toLocaleString()}원</span>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <p class="text-sm text-muted-foreground">입력 토큰: ${result.token_info.input_tokens.toLocaleString()}</p>
                                <p class="text-sm text-muted-foreground">출력 토큰: ${result.token_info.output_tokens.toLocaleString()}</p>
                            </div>
                            <div>
                                <p class="text-sm text-muted-foreground">모델: ${result.token_info.model || 'gpt-4o-mini'}</p>
                                <p class="text-sm text-muted-foreground">처리 시간: ${result.token_info.processing_time?.toFixed(2) || '0.00'}초</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 모달 추가 및 표시
        document.body.appendChild(resultModal);
        document.body.classList.add('modal-open');
        
        // 페이드 인 효과
        setTimeout(() => {
            resultModal.style.opacity = '1';
        }, 10);
        
        // 닫기 버튼 이벤트
        const closeResultBtn = resultModal.querySelector('#close-result-modal');
        closeResultBtn.addEventListener('click', function() {
            closeResultModal();
        });
        
        // 외부 클릭 시 닫기
        resultModal.addEventListener('click', function(e) {
            if (e.target === resultModal) {
                closeResultModal();
            }
        });
        
        // 결과 복사 기능
        const copyResultBtn = resultModal.querySelector('#copy-result');
        copyResultBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(result.content)
                .then(() => {
                    // 복사 성공 시 버튼 텍스트 변경
                    copyResultBtn.innerHTML = '<i class="fas fa-check mr-1"></i>복사됨';
                    setTimeout(() => {
                        copyResultBtn.innerHTML = '<i class="fas fa-copy mr-1"></i>복사';
                    }, 2000);
                })
                .catch(err => {
                    console.error('복사 실패:', err);
                    alert('텍스트 복사에 실패했습니다.');
                });
        });
    }
    
    // 결과 모달 닫기 함수
    function closeResultModal() {
        const resultModal = document.getElementById('result-modal');
        if (resultModal) {
            resultModal.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(resultModal);
                document.body.classList.remove('modal-open');
            }, 300);
        }
    }

    // 보고서 생성 API 호출
    generateReport.addEventListener('click', async function() {
        const userInput = reportInput.value.trim();
        
        if (userInput.length < 10) {
            alert('보고서 내용을 최소 10자 이상 입력해주세요.');
            return;
        }
        
        if (selectedTemplates.length === 0) {
            alert('선택된 템플릿이 없습니다.');
            return;
        }
        
        // 로딩 상태 표시
        generateReport.disabled = true;
        generateReport.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>생성 중...';
        
        try {
            const templateIds = selectedTemplates.map(template => template.id);
            
            const response = await fetch('/api/drafts/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    template_ids: templateIds,
                    user_input: userInput
                }),
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `API 요청 실패: ${response.status}`;
                
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.error) {
                        errorMessage = errorJson.error;
                    }
                } catch (e) {
                    if (errorText) {
                        errorMessage += ` - ${errorText}`;
                    }
                }
                
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            
            // 보고서 생성 결과 처리 및 표시
            displayGeneratedReport(result);
            
            // 모달 닫기
            closeReportModalWithAnimation();
            
        } catch (error) {
            console.error('보고서 생성 중 오류:', error);
            alert(`보고서 생성 중 오류가 발생했습니다: ${error.message}`);
        } finally {
            // 버튼 상태 복원
            generateReport.disabled = false;
            generateReport.innerHTML = '생성하기';
        }
    });
    
    // 테마 토글 기능 초기화
    function initializeThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        
        // 저장된 테마 확인 및 적용
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
        
        // 테마 토글 클릭 이벤트
        themeToggle.addEventListener('click', function() {
            if (document.body.classList.contains('dark')) {
                // 다크 모드 -> 라이트 모드
                document.body.classList.remove('dark');
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
                localStorage.setItem('theme', 'light');
            } else {
                // 라이트 모드 -> 다크 모드
                document.body.classList.add('dark');
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
                localStorage.setItem('theme', 'dark');
            }
        });
    }
});

// 템플릿 관련 함수들은 template.js로 이동
// API 호출 관련 함수들은 api.js로 이동 