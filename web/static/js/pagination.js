/**
 * 페이지네이션 업데이트 함수
 * @param {number} currentPage - 현재 페이지 번호
 * @param {number} totalPages - 전체 페이지 수
 */
function updatePagination(currentPage, totalPages) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    if (totalPages <= 1) {
        pagination.classList.add('hidden');
        return;
    }
    
    pagination.classList.remove('hidden');
    
    // 처음 페이지로 이동 버튼
    if (currentPage > 1) {
        addPaginationButton(pagination, 1, '처음', currentPage);
    }
    
    // 이전 페이지 버튼
    if (currentPage > 1) {
        addPaginationButton(pagination, currentPage - 1, '이전', currentPage);
    }
    
    // 페이지 번호 버튼
    const maxPageButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPageButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxPageButtons - 1);
    
    if (endPage - startPage + 1 < maxPageButtons) {
        startPage = Math.max(1, endPage - maxPageButtons + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        addPaginationButton(pagination, i, i.toString(), currentPage);
    }
    
    // 다음 페이지 버튼
    if (currentPage < totalPages) {
        addPaginationButton(pagination, currentPage + 1, '다음', currentPage);
    }
    
    // 마지막 페이지로 이동 버튼
    if (currentPage < totalPages) {
        addPaginationButton(pagination, totalPages, '마지막', currentPage);
    }
}

/**
 * 페이지네이션 버튼 추가 함수
 * @param {HTMLElement} pagination - 페이지네이션 컨테이너 요소
 * @param {number} page - 버튼이 가리키는 페이지 번호
 * @param {string} text - 버튼에 표시될 텍스트
 * @param {number} currentPage - 현재 페이지 번호
 */
function addPaginationButton(pagination, page, text, currentPage) {
    const button = document.createElement('button');
    button.textContent = text;
    
    // 기본 버튼 스타일
    button.className = 'px-3 py-2 rounded text-sm transition-colors';
    
    // 현재 페이지인 경우 더 강조된 스타일 적용
    if (page === currentPage) {
        button.classList.add('bg-primary', 'text-primary-foreground', 'font-medium', 'shadow-md', 'transform', 'scale-110');
        button.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
        button.style.fontWeight = '600';
    } else {
        button.classList.add('hover:bg-muted', 'text-muted-foreground', 'hover:text-card-foreground');
    }
    
    button.addEventListener('click', () => {
        if (page !== currentPage) {
            // 로딩 상태 리셋
            const loading = document.getElementById('loading');
            loading.classList.remove('active', 'complete');
            
            // 페이지 전환 시 약간의 지연으로 DOM 업데이트 보장
            setTimeout(() => {
                fetchTemplates(page);
            }, 50);
        }
    });
    
    pagination.appendChild(button);
} 