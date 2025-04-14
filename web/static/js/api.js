/**
 * 템플릿 검색 API 호출 함수
 * @param {number} page - 페이지 번호
 */
async function fetchTemplates(page = 1) {
    const searchInput = document.getElementById('search-input');
    const docTypeSelect = document.getElementById('doc_type');
    const managerInput = document.getElementById('manager-input');
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
        loading.style.display = 'flex';
        loading.classList.add('active');
        loading.classList.remove('complete');
    }

    // 로딩 종료 함수 (파일 최상단 또는 별도 모듈로 이동 가능)
    function hideLoading() {
        if (!loading) return;
        loading.classList.remove('active');
        loading.classList.add('complete');
        // style.display = 'none' 은 CSS의 .loading.complete 에서 처리하도록 유도 가능
        // 여기서는 명시적으로 none 처리 유지
        loading.style.display = 'none';
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
        
        // 보도자료인 경우 manager 파라미터 추가 (값이 없으면 '%' 사용)
        if (docType === "press") {
            const managerValue = managerInput.value.trim();
            const managerParam = managerValue ? managerValue : '%'; // 값이 없으면 '%' 사용
            url += `&manager=${encodeURIComponent(managerParam)}`;
        }

        // 정렬 기준 파라미터 제거됨
        
        const response = await fetch(url);
        
        clearTimeout(loadingTimeout); // 성공 시 타임아웃 취소
        
        if (!response.ok) {
            throw new Error(`API 요청 실패: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 검색 결과 및 페이지네이션 표시
        if (data.items && data.items.length > 0) {
            // 초기 메시지 숨기기
            if (initialMessage) initialMessage.classList.add('hidden');
            if (noResults) noResults.classList.add('hidden');
            
            // 클라이언트 측 정렬 로직 제거됨

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
            // 검색 결과 없음
            if (initialMessage) initialMessage.classList.add('hidden');
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