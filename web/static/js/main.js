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
        
        // 초기 메시지 즉시 숨기기
        if (initialMessage) {
            initialMessage.classList.add('hidden');
        }
        
        // 로딩 표시기 보이기 - display 스타일 대신 클래스 사용
        if (loading) {
            loading.classList.remove('hidden');
        }
        
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
        
        // 분석 결과 섹션 숨기기
        const analysisSection = document.getElementById('template-analysis-section');
        if (analysisSection) {
            analysisSection.classList.add('hidden');
        }
        
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
            loadingMessage.className = 'fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4'; /* 패딩 추가 */
            loadingMessage.innerHTML = `
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md border border-gray-200 dark:border-gray-700"> {/* 명시적 배경색, 그림자 강화, 테두리 추가 */}
                    <div class="flex flex-col items-center">
                        {/* 스피너 색상 변경: 라이트 모드에서 더 잘 보이도록 */}
                        <div class="animate-spin rounded-full h-12 w-12 border-4 border-gray-500 dark:border-gray-400 border-t-transparent mb-4"></div>
                        {/* 텍스트 색상 명시 */}
                        <p class="text-lg font-medium text-gray-900 dark:text-white">템플릿 내용 분석 중...</p>
                        {/* 텍스트 색상 명시 */}
                        <p class="text-sm text-gray-600 dark:text-gray-400 mt-2 text-center">문서 구조, 어조, 핵심 키워드를 추출하고 있습니다.</p>
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
            
            // 분석 결과 파일을 가져와서 모달에 표시
            await fetchAndDisplayAnalysisResult(result.output_file);
            
        } catch (error) {
            console.error('템플릿 내용 분석 중 오류:', error);
            alert(`템플릿 내용 분석 중 오류가 발생했습니다: ${error.message}`);
        }
    }

    /**
     * 템플릿 분석 결과 파일을 가져와서 모달에 표시하는 함수
     * @param {string} analysisFilePath - 분석 결과 파일 경로
     */
    async function fetchAndDisplayAnalysisResult(analysisFilePath) {
        try {
            // 파일 이름에서 경로 부분 제거 (Windows 경로도 처리)
            let fileName = analysisFilePath.split('/').pop();
            // Windows 경로인 경우 추가 처리 (드라이브 문자와 : 제거)
            if (fileName.includes('\\') || fileName.includes(':')) {
                fileName = fileName.split('\\').pop(); // 백슬래시로 분리
                fileName = fileName.replace(/^[a-zA-Z]:/, ''); // 'c:' 같은 드라이브 문자 제거
            }
            
            // 로그 출력
            console.log(`분석 결과 파일 가져오기: ${fileName}`);
            
            // 분석 결과를 가져오기 위한 재시도 로직
            let analysisData = null;
            let attempts = 0;
            const maxAttempts = 5; // 최대 5번 시도
            const initialDelay = 500; // 첫 시도는 0.5초 후
            
            // 재시도 함수
            const fetchWithRetry = async (attempt) => {
                try {
                    // 재시도 시 지연 시간 증가 (백오프 전략)
                    const delay = initialDelay * Math.pow(1.5, attempt);
                    
                    if (attempt > 0) {
                        console.log(`분석 결과 파일 가져오기 ${attempt}번째 시도 (${delay}ms 지연)...`);
                    }
                    
                    // 지정된 시간만큼 대기
                    await new Promise(resolve => setTimeout(resolve, delay));
                    
                    const response = await fetch(`/api/drafts/analysis/${fileName}`);
                    
                    if (!response.ok) {
                        if (response.status === 404 && attempt < maxAttempts - 1) {
                            // 파일을 찾을 수 없는 경우 다시 시도
                            return null;
                        }
                        throw new Error(`분석 결과 파일을 가져올 수 없습니다: ${response.status}`);
                    }
                    
                    return await response.json();
                } catch (error) {
                    if (attempt < maxAttempts - 1) {
                        // 아직 재시도 가능한 경우
                        console.error(`분석 결과 가져오기 실패 (시도 ${attempt + 1}/${maxAttempts}): ${error.message}`);
                        return null;
                    }
                    throw error; // 최대 시도 횟수 초과 시 에러 던지기
                }
            };
            
            // 처음부터 maxAttempts까지 시도
            for (attempts = 0; attempts < maxAttempts; attempts++) {
                analysisData = await fetchWithRetry(attempts);
                if (analysisData) {
                    // 성공적으로 데이터를 가져오면 반복 중단
                    break;
                }
            }
            
            // 모든 시도 실패 시
            if (!analysisData) {
                throw new Error(`${maxAttempts}번의 시도 후에도 분석 결과 파일을 가져올 수 없습니다.`);
            }
            
            // 분석 결과 섹션 요소 참조
            const analysisSection = document.getElementById('template-analysis-section');
            const analysisContent = document.getElementById('template-analysis-content');
            
            // 분석 결과가 있는지 확인
            if (analysisData && analysisData.templates && analysisData.templates.length > 0) {
                // 분석 섹션 표시
                analysisSection.classList.remove('hidden');
                
                // 분석 결과 HTML 생성
                let analysisHtml = `
                    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden">
                        <div class="p-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                            <h3 class="text-md font-semibold text-gray-900 dark:text-white">분석된 템플릿 (${analysisData.templates.length}개)</h3>
                            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">템플릿의 구조와 핵심 키워드가 추출되었습니다.</p>
                        </div>
                        
                        <div class="divide-y divide-gray-200 dark:divide-gray-700">
                `;
                
                // 각 템플릿에 대한 정보 표시
                analysisData.templates.forEach((template, index) => {
                    analysisHtml += `
                        <div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                            <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                                <!-- 제목 및 섹션 정보 -->
                                <div class="flex-1">
                                    <h4 class="font-semibold text-gray-900 dark:text-white text-base mb-2">${template.title}</h4>
                                    
                                    <div class="mb-3">
                                        <div class="flex items-center mb-1.5">
                                            <span class="inline-flex items-center justify-center bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 rounded text-xs font-medium px-2 py-0.5 mr-2">
                                                <svg class="w-3 h-3 mr-1" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                                                    <path d="M3 4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4z"/>
                                                    <path d="M3 10a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-2z"/>
                                                    <path d="M3 16a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-2z"/>
                                                </svg>
                                                주요 섹션
                                            </span>
                                            ${template.structure.length > 4 ? 
                                                `<span class="text-xs text-gray-500 dark:text-gray-400">(${template.structure.length}개 섹션 중 주요 4개 표시)</span>` : 
                                                `<span class="text-xs text-gray-500 dark:text-gray-400">(총 ${template.structure.length}개 섹션)</span>`
                                            }
                                        </div>
                                        
                                        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                                            ${template.structure.slice(0, 4).map((section, sectionIndex) => 
                                                `<div class="flex items-center bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2 rounded-md">
                                                    <span class="inline-flex items-center justify-center bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-300 rounded-full w-5 h-5 text-xs font-medium mr-2">${sectionIndex + 1}</span>
                                                    <span class="text-sm text-gray-700 dark:text-gray-300 truncate">${section.name}</span>
                                                </div>`
                                            ).join('')}
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- 키워드 정보 -->
                                <div class="md:w-1/3">
                                    <div class="flex items-center mb-1.5">
                                        <span class="inline-flex items-center justify-center bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300 rounded text-xs font-medium px-2 py-0.5">
                                            <svg class="w-3 h-3 mr-1" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                                                <path fill-rule="evenodd" d="M3 5a1 1 0 0 1 1-1h12a1 1 0 1 1 0 2H4a1 1 0 0 1-1-1zm1 3a1 1 0 1 0 0 2h12a1 1 0 1 0 0-2H4zm0 4a1 1 0 1 0 0 2h12a1 1 0 1 0 0-2H4z" clip-rule="evenodd" />
                                            </svg>
                                            키워드
                                        </span>
                                    </div>
                                    <div class="flex flex-wrap gap-2">
                                        ${template.keywords.map(keyword => 
                                            `<span class="text-xs bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 px-2 py-1 rounded-md">
                                                ${keyword}
                                            </span>`
                                        ).join('')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                analysisHtml += `
                        </div>
                    </div>
                    <div class="text-right mt-2">
                        <button id="toggle-template-detail" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                            모든 섹션 보기/접기
                        </button>
                    </div>
                `;
                
                // 분석 결과 내용 업데이트
                analysisContent.innerHTML = analysisHtml;
                
                // 모든 섹션 보기/접기 토글 버튼 이벤트 리스너 추가
                const toggleButton = document.getElementById('toggle-template-detail');
                if (toggleButton) {
                    toggleButton.addEventListener('click', function() {
                        const detailView = document.querySelector('.template-detail-view');
                        if (detailView) {
                            detailView.classList.toggle('hidden');
                            this.textContent = detailView.classList.contains('hidden') ? 
                                '모든 섹션 보기' : '섹션 접기';
                        }
                    });
                }
            } else {
                // 분석 결과가 없는 경우
                analysisContent.innerHTML = '<p class="text-muted-foreground italic">분석 결과가 없습니다.</p>';
                analysisSection.classList.remove('hidden');
            }
            
        } catch (error) {
            console.error('분석 결과 표시 중 오류:', error);
            // 오류 시에도 섹션은 표시하고 오류 메시지 표시
            const analysisSection = document.getElementById('template-analysis-section');
            const analysisContent = document.getElementById('template-analysis-content');
            
            analysisContent.innerHTML = `<p class="text-red-500">분석 결과를 가져오는 중 오류가 발생했습니다: ${error.message}</p>`;
            analysisSection.classList.remove('hidden');
        }
    }

    /**
     * 생성된 보고서를 화면에 표시하는 함수
     * @param {Object} result - API로부터 받은 결과 객체
     */
    function displayGeneratedReport(result) {
        // 모달 배경 생성
        const modalBackground = document.createElement('div');
        modalBackground.id = 'resultModalBackground';
        modalBackground.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 opacity-0 transition-opacity duration-300';
        modalBackground.style.backdropFilter = 'blur(2px)';

        // 모달 콘텐츠 생성
        const modalContent = document.createElement('div');
        modalContent.id = 'resultModalContent';
        modalContent.className = 'bg-white dark:bg-gray-800 rounded-lg shadow-xl w-11/12 max-w-3xl max-h-[85vh] overflow-y-auto p-6 transform -translate-y-4 transition-transform duration-300';

        // 제목 및 설명
        const header = document.createElement('div');
        header.className = 'mb-6';
        header.innerHTML = `
            <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">생성된 보고서</h2>
            <p class="text-gray-600 dark:text-gray-300">AI가 생성한 보고서 내용입니다.</p>
        `;
        modalContent.appendChild(header);

        // 보고서 내용 표시
        const reportContent = document.createElement('div');
        reportContent.className = 'mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-md whitespace-pre-wrap text-gray-800 dark:text-gray-100';
        reportContent.style.maxHeight = '50vh';
        reportContent.style.overflow = 'auto';
        reportContent.style.fontFamily = 'Pretendard, sans-serif';
        reportContent.textContent = result.report.content || '보고서 내용이 없습니다.';
        modalContent.appendChild(reportContent);

        // 파일 정보 표시 (있는 경우)
        if (result.resultFile) {
            const fileSection = document.createElement('div');
            fileSection.className = 'mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md';
            
            fileSection.innerHTML = `
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100">저장된 파일</h3>
                        <p class="text-gray-600 dark:text-gray-300 text-sm">${result.resultFile}</p>
                    </div>
                    <button id="downloadReportBtn" class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center">
                        <i class="fas fa-download mr-2"></i>다운로드
                    </button>
                </div>
            `;
            
            modalContent.appendChild(fileSection);
        }

        // 토큰 사용량 섹션
        const tokenSection = document.createElement('div');
        tokenSection.className = 'mb-6';
        
        const tokenInfo = result.report.token_usage || {};
        
        tokenSection.innerHTML = `
            <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">토큰 사용량</h3>
            <div class="grid grid-cols-2 gap-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-md">
                <div>
                    <p class="text-sm text-gray-600 dark:text-gray-300">입력 토큰</p>
                    <p class="text-gray-800 dark:text-gray-100">${tokenInfo.input_tokens || 0}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600 dark:text-gray-300">출력 토큰</p>
                    <p class="text-gray-800 dark:text-gray-100">${tokenInfo.output_tokens || 0}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600 dark:text-gray-300">총 토큰</p>
                    <p class="text-gray-800 dark:text-gray-100">${tokenInfo.total_tokens || 0}</p>
                </div>
                <div>
                    <p class="text-sm text-gray-600 dark:text-gray-300">비용</p>
                    <p class="text-gray-800 dark:text-gray-100">${tokenInfo.cost ? tokenInfo.cost.toFixed(2) + '원' : '0원'}</p>
                </div>
            </div>
        `;
        
        modalContent.appendChild(tokenSection);

        // 버튼 섹션
        const buttonSection = document.createElement('div');
        buttonSection.className = 'flex justify-end gap-4';
        
        const copyButton = document.createElement('button');
        copyButton.className = 'px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white rounded hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors';
        copyButton.textContent = '내용 복사';
        copyButton.onclick = () => {
            navigator.clipboard.writeText(result.report.content || '')
                .then(() => {
                    copyButton.textContent = '복사됨!';
                    setTimeout(() => {
                        copyButton.textContent = '내용 복사';
                    }, 2000);
                })
                .catch(err => {
                    console.error('클립보드 복사 실패:', err);
                    copyButton.textContent = '복사 실패';
                    setTimeout(() => {
                        copyButton.textContent = '내용 복사';
                    }, 2000);
                });
        };
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors';
        closeBtn.textContent = '닫기';
        closeBtn.onclick = closeResultModal;
        
        buttonSection.appendChild(copyButton);
        buttonSection.appendChild(closeBtn);
        modalContent.appendChild(buttonSection);

        // 모달을 페이지에 추가
        modalBackground.appendChild(modalContent);
        document.body.appendChild(modalBackground);

        // 모달 외부 클릭 시 닫기
        modalBackground.addEventListener('click', (e) => {
            if (e.target === modalBackground) {
                closeResultModal();
            }
        });

        // 다운로드 버튼 이벤트 리스너 추가
        if (result.resultFile) {
            setTimeout(() => {
                const downloadBtn = document.getElementById('downloadReportBtn');
                if (downloadBtn) {
                    downloadBtn.addEventListener('click', () => {
                        window.location.href = `/download/${result.resultFile}`;
                    });
                }
            }, 0);
        }

        // 모달 표시 애니메이션
        setTimeout(() => {
            modalBackground.style.opacity = '1';
            modalContent.style.transform = 'translateY(0)';
        }, 10);
    }
    
    /**
     * 결과 모달 닫기 함수
     */
    function closeResultModal() {
        const modal = document.getElementById('resultModalBackground');
        // 페이드 아웃 효과
        modal.style.opacity = '0';
        modal.firstElementChild.style.transform = 'translateY(-4rem)';
        
        // 애니메이션 후 제거
        setTimeout(() => {
            document.body.removeChild(modal);
        }, 300);
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