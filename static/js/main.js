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
    const managerInputContainer = document.getElementById('manager-input-container');
    const managerInput = document.getElementById('manager-input');
    const managerRequired = document.getElementById('manager-required');
    
    // 보고서 관련 DOM 요소 참조
    const generateReportBtn = document.getElementById('generate-report-btn');
    const reportModal = document.getElementById('report-modal');
    const closeReportModal = document.getElementById('close-report-modal');
    const cancelReport = document.getElementById('cancel-report');
    const generateReport = document.getElementById('generate-report');
    const reportInput = document.getElementById('report-input');
    const characterCount = document.getElementById('character-count');
    const clearSelectionsBtn = document.getElementById('clear-selections');
    
    // 상태 변수
    let currentPage = 1;
    let totalPages = 1;
    // let selectedTemplate = null; // template.js 에서만 사용되므로 여기서 제거
    
    // 테마 토글 초기화
    initializeThemeToggle();
    
    // 문서 유형에 따라 담당자 필드 보이기/숨기기
    docTypeSelect.addEventListener('change', function() {
        const selectedDocType = this.value;
        
        if (selectedDocType === 'press') {
            managerInputContainer.classList.remove('hidden');
            managerRequired.classList.remove('hidden');
        } else {
            managerInputContainer.classList.add('hidden');
            managerRequired.classList.add('hidden');
        }
    });
    
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
        
        // 보도자료인 경우 담당자 필수 확인
        if (docType === 'press' && !managerInput.value.trim()) {
            alert('보도자료 검색 시 담당자 정보가 필요합니다.');
            managerInput.focus();
            return;
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

    // 보고서 생성 API 호출
    generateReport.addEventListener('click', async function() {
        const userInput = reportInput.value.trim();
        
        if (!userInput) {
            alert('보고서 정보를 입력해주세요.');
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
                throw new Error(`API 요청 실패: ${response.status}`);
            }
            
            const result = await response.json();
            
            // 성공 메시지
            alert('보고서가 생성되었습니다.');
            
            // 모달 닫기
            closeReportModalWithAnimation();
            
            // TODO: 생성된 보고서 결과 처리
            console.log('생성된 보고서:', result);
            
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
            document.documentElement.classList.add('dark');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
        
        // 테마 토글 클릭 이벤트
        themeToggle.addEventListener('click', function() {
            if (document.documentElement.classList.contains('dark')) {
                // 다크 모드 -> 라이트 모드
                document.documentElement.classList.remove('dark');
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
                localStorage.setItem('theme', 'light');
            } else {
                // 라이트 모드 -> 다크 모드
                document.documentElement.classList.add('dark');
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
                localStorage.setItem('theme', 'dark');
            }
        });
    }
});

// 템플릿 관련 함수들은 template.js로 이동
// API 호출 관련 함수들은 api.js로 이동 