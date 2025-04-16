/**
 * 템플릿 검색 API 호출 함수
 * @param {number} page - 페이지 번호
 */
async function fetchTemplates(page = 1) {
    const searchInput = document.getElementById('search-input');
    const docTypeSelect = document.getElementById('doc_type');
    // const sortBySelect = document.getElementById('sort-by'); // 정렬 기준 제거됨
    const initialMessage = document.getElementById('initial-message');
    const noResults = document.getElementById('no-results');
    const searchResults = document.getElementById('templates-container');
    
    const keyword = searchInput.value.trim();
    const docType = docTypeSelect.value;
    const currentPage = page;
    const perPage = 12; // 페이지당 표시할 항목 수
    
    const loading = document.getElementById('loading'); // 로딩 요소 참조

    // 로딩 시작 함수
    function showLoading() {
        if (!loading) return;
        loading.classList.remove('hidden');
        loading.classList.add('active');
        loading.classList.remove('complete');
    }

    // 로딩 종료 함수 (파일 최상단 또는 별도 모듈로 이동 가능)
    function hideLoading() {
        if (!loading) return;
        loading.classList.remove('active');
        loading.classList.add('complete');
        loading.classList.add('hidden');
    }

    showLoading(); // 로딩 시작

    // API 타임아웃 처리 (10초)
    const loadingTimeout = setTimeout(() => {
        console.warn("API 요청 시간이 초과되었습니다.");
        hideLoading();
        // 필요시 사용자에게 타임아웃 메시지 표시
        const noResults = document.getElementById('no-results');
        if (noResults) {
             noResults.innerHTML = `<div class="text-center py-10 text-orange-500">요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.</div>`;
             noResults.classList.remove('hidden');
             // 다른 결과 영역 숨기기
             document.getElementById('templates-container').classList.add('hidden');
             document.getElementById('pagination').classList.add('hidden');
             document.getElementById('search-summary').classList.add('hidden');
        }
    }, 10000);
    
    try {
        // API 요청 생성
        let url = `/api/search?page=${currentPage}&per_page=${perPage}`;
        
        if (keyword) {
            url += `&keyword=${encodeURIComponent(keyword)}`;
        }
        
        if (docType && docType !== "all") {
            url += `&doc_type=${encodeURIComponent(docType)}`;
        }
        
        // 담당자 검색 조건은 항상 '%'로 설정
        url += `&manager=${encodeURIComponent('%')}`;

        // 정렬 기준 파라미터 제거됨
        
        const response = await fetch(url);
        
        clearTimeout(loadingTimeout); // 성공 시 타임아웃 취소
        
        if (!response.ok) {
            throw new Error(`API 요청 실패: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 검색 결과 및 페이지네이션 표시
        if (data.items && data.items.length > 0) {
            // 초기 메시지와 결과 없음 메시지 모두 숨기기
            if (initialMessage) initialMessage.classList.add('hidden'); // 이미 숨겨져 있더라도 확실하게
            if (noResults) noResults.classList.add('hidden');
            
            // API에서 받은 순서 그대로 템플릿 렌더링
            renderTemplates(data.items);
            
            // 페이지네이션 업데이트
            updatePagination(currentPage, Math.ceil(data.totalCount / perPage));
            
            // 검색 결과 메시지 업데이트
            const resultCount = document.getElementById('result-count');
            if (resultCount) {
                resultCount.textContent = `${data.totalCount}`;
                document.getElementById('search-summary').classList.remove('hidden');
            }
            
            // 검색 결과 및 페이지네이션 표시
            searchResults.classList.remove('hidden');
            document.getElementById('pagination').classList.remove('hidden');
            
            hideLoading(); // 성공 시 로딩 종료
        } else {
            // 검색 결과 없음 - 초기 메시지는 계속 숨겨진 상태 유지
            if (initialMessage) initialMessage.classList.add('hidden'); // 이미 숨겨져 있더라도 확실하게
            if (noResults) noResults.classList.remove('hidden');
            
            // 검색 결과 및 페이지네이션 숨기기
            searchResults.classList.add('hidden');
            document.getElementById('pagination').classList.add('hidden');
            document.getElementById('search-summary').classList.add('hidden');
            
            hideLoading(); // 결과 없을 시 로딩 종료
        }
        
    } catch (error) {
        console.error('API 요청 중 오류 발생:', error);
        
        clearTimeout(loadingTimeout); // 오류 발생 시 타임아웃 취소
        
        // 오류 메시지 표시
        if (initialMessage) initialMessage.classList.add('hidden');
        if (noResults) noResults.classList.remove('hidden');
        noResults.innerHTML = `<div class="text-center py-10 text-red-500">오류가 발생했습니다: ${error.message}</div>`;
        
        // 검색 결과 및 페이지네이션 숨기기
        searchResults.classList.add('hidden');
        document.getElementById('pagination').classList.add('hidden');
        document.getElementById('search-summary').classList.add('hidden');
        
        hideLoading(); // 오류 발생 시 로딩 종료
    }
} 