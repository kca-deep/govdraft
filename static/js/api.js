/**
 * 템플릿 검색 API 호출 함수
 * @param {number} page - 페이지 번호
 */
async function fetchTemplates(page = 1) {
    const searchInput = document.getElementById('search-input');
    const docTypeSelect = document.getElementById('doc_type');
    const managerInput = document.getElementById('manager-input');
    const initialMessage = document.getElementById('initial-message');
    const noResults = document.getElementById('no-results');
    const searchResults = document.getElementById('templates-container');
    
    const keyword = searchInput.value.trim();
    const docType = docTypeSelect.value;
    const currentPage = page;
    const perPage = 12; // 페이지당 표시할 항목 수
    
    // 로딩 상태 활성화
    const loading = document.getElementById('loading');
    loading.style.display = 'flex';
    loading.classList.add('active');
    loading.classList.remove('complete');
    
    // 10초 후에 자동으로 로딩 표시 종료 (API 응답 없을 경우 대비)
    const loadingTimeout = setTimeout(() => {
        hideLoading();
    }, 10000);
    
    // 로딩 숨김 함수
    function hideLoading() {
        loading.classList.remove('active');
        loading.classList.add('complete');
        loading.style.display = 'none';
    }
    
    try {
        // API 요청 생성
        let url = `/search?page=${currentPage}&per_page=${perPage}`;
        
        if (keyword) {
            url += `&keyword=${encodeURIComponent(keyword)}`;
        }
        
        if (docType && docType !== "all") {
            url += `&doc_type=${encodeURIComponent(docType)}`;
        }
        
        // 보도자료인 경우 manager 파라미터 추가
        if (docType === "press" && managerInput.value.trim()) {
            url += `&manager=${encodeURIComponent(managerInput.value.trim())}`;
        }
        
        const response = await fetch(url);
        
        // 로딩 타임아웃 취소
        clearTimeout(loadingTimeout);
        
        if (!response.ok) {
            throw new Error(`API 요청 실패: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 검색 결과 및 페이지네이션 표시
        if (data.items && data.items.length > 0) {
            // 초기 메시지 숨기기
            if (initialMessage) initialMessage.classList.add('hidden');
            if (noResults) noResults.classList.add('hidden');
            
            // 템플릿 렌더링
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
            
            // 로딩 상태 즉시 비활성화
            hideLoading();
        } else {
            // 검색 결과 없음
            if (initialMessage) initialMessage.classList.add('hidden');
            if (noResults) noResults.classList.remove('hidden');
            
            // 검색 결과 및 페이지네이션 숨기기
            searchResults.classList.add('hidden');
            document.getElementById('pagination').classList.add('hidden');
            document.getElementById('search-summary').classList.add('hidden');
            
            // 로딩 상태 즉시 비활성화
            hideLoading();
        }
        
    } catch (error) {
        console.error('API 요청 중 오류 발생:', error);
        
        // 로딩 타임아웃 취소
        clearTimeout(loadingTimeout);
        
        // 오류 메시지 표시
        if (initialMessage) initialMessage.classList.add('hidden');
        if (noResults) noResults.classList.remove('hidden');
        noResults.innerHTML = `<div class="text-center py-10 text-red-500">오류가 발생했습니다: ${error.message}</div>`;
        
        // 검색 결과 및 페이지네이션 숨기기
        searchResults.classList.add('hidden');
        document.getElementById('pagination').classList.add('hidden');
        document.getElementById('search-summary').classList.add('hidden');
        
        // 로딩 상태 즉시 비활성화
        hideLoading();
    }
} 