// 전역 상태 변수
let selectedTemplates = [];
let selectedTemplate = null;

/**
 * 템플릿 렌더링 함수
 * @param {Array} templates - 템플릿 데이터 배열
 */
function renderTemplates(templates) {
    const searchResults = document.getElementById('templates-container');
    searchResults.innerHTML = '';
    
    if (templates.length === 0) {
        searchResults.innerHTML = '<div class="text-center py-10 text-muted-foreground">검색 결과가 없습니다.</div>';
        return;
    }
    
    templates.forEach((template, index) => {
        const cardElement = document.createElement('div');
        cardElement.className = 'template-card bg-card rounded-lg border shadow-sm hover-lift theme-transition fade-in';
        cardElement.style.animationDelay = `${index * 50}ms`;
        cardElement.dataset.templateId = template.id;
        
        // 표 태그 제거 및 텍스트 추출
        const tempElement = document.createElement('div');
        tempElement.innerHTML = template.desc || template.content || template.description || '';
        
        // 표 태그 포함 여부 확인 및 처리
        const hasTables = tempElement.querySelectorAll('table').length > 0;
        let cleanDescription = '';
        
        if (hasTables) {
            cleanDescription = '표 내용 생략... ';
            const textNodes = Array.from(tempElement.childNodes)
                .filter(node => node.nodeName !== 'TABLE')
                .map(node => node.textContent.trim())
                .filter(text => text.length > 0);
            cleanDescription += textNodes.join(' ');
        } else {
            cleanDescription = tempElement.textContent.trim();
        }
        
        // 텍스트 길이 제한
        if (cleanDescription.length > 150) {
            cleanDescription = cleanDescription.substring(0, 150) + '...';
        }
        
        // 선택된 템플릿 여부 확인
        const isSelected = selectedTemplates.some(item => item.id === template.id);
        
        cardElement.innerHTML = `
            <div class="p-4 flex flex-col h-full">
                <div class="flex justify-between items-start mb-2">
                    <span class="badge badge-primary theme-transition">${template.docType || '문서'}</span>
                    <div class="flex items-center space-x-2">
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" class="template-checkbox sr-only" data-template-id="${template.id}" ${isSelected ? 'checked' : ''}>
                            <span class="checkbox-custom ${isSelected ? 'checked' : ''} flex items-center justify-center transition-colors">
                                <i class="fas fa-check text-white ${isSelected ? '' : 'opacity-0'}"></i>
                            </span>
                        </label>
                        <span class="text-muted-foreground text-sm">${template.date ? new Date(template.date).toLocaleDateString('ko-KR') : '날짜 정보 없음'}</span>
                    </div>
                </div>
                <h3 class="text-md font-semibold text-card-foreground mb-2 line-clamp-2 cursor-pointer hover:text-primary transition-colors">${template.title || '제목 없음'}</h3>
                <p class="text-muted-foreground text-xs mb-3 line-clamp-3 flex-grow">${cleanDescription}</p>
                <div class="flex justify-between items-center mt-auto pt-2 border-t border-border theme-transition">
                    <span class="text-muted-foreground text-xs">${template.ministry || '부처 정보 없음'}</span>
                    <button class="view-template-btn text-primary hover:text-primary-focus text-xs font-medium transition-colors">
                        <span class="relative">
                            자세히 보기
                            <span class="absolute bottom-0 left-0 w-0 h-[1px] bg-primary group-hover:w-full transition-all"></span>
                        </span>
                    </button>
                </div>
            </div>
        `;
        
        // 템플릿 상세보기 이벤트 - 자세히 보기 버튼
        const viewButton = cardElement.querySelector('.view-template-btn');
        viewButton.addEventListener('click', function() {
            selectedTemplate = template;
            showTemplateDetail(template);
        });
        
        // 템플릿 상세보기 이벤트 - 제목 클릭
        const titleElement = cardElement.querySelector('h3');
        titleElement.addEventListener('click', function() {
            selectedTemplate = template;
            showTemplateDetail(template);
        });
        
        // 템플릿 선택 이벤트
        const checkbox = cardElement.querySelector('.template-checkbox');
        const checkboxCustom = cardElement.querySelector('.checkbox-custom');
        const checkIcon = cardElement.querySelector('.fa-check');
        
        checkbox.addEventListener('change', function() {
            if (checkbox.checked) {
                if (selectedTemplates.length >= 5) {
                    checkbox.checked = false;
                    alert('최대 5개까지 템플릿을 선택할 수 있습니다.');
                    return;
                }
                checkboxCustom.classList.add('bg-primary', 'checked');
                checkIcon.classList.remove('opacity-0');
                cardElement.classList.add('selected');
                addSelectedTemplate(template);
            } else {
                checkboxCustom.classList.remove('bg-primary', 'checked');
                checkIcon.classList.add('opacity-0');
                cardElement.classList.remove('selected');
                removeSelectedTemplate(template.id);
            }
        });
        
        // 이미 선택된 템플릿인 경우 스타일 적용
        if (isSelected) {
            checkboxCustom.classList.add('bg-primary', 'checked');
            checkIcon.classList.remove('opacity-0');
            cardElement.classList.add('selected');
        }
        
        searchResults.appendChild(cardElement);
    });
    
    // 결과를 표시한 후 검색 결과 컨테이너 표시
    searchResults.classList.remove('hidden');
    
    // 선택된 템플릿 상태 업데이트
    updateSelectedTemplatesUI();
}

/**
 * 선택된 템플릿 추가 함수
 * @param {Object} template - 추가할 템플릿 객체
 */
function addSelectedTemplate(template) {
    // 이미 선택된 템플릿인지 확인
    if (selectedTemplates.some(item => item.id === template.id)) {
        return;
    }
    
    // 최대 5개까지만 선택 가능
    if (selectedTemplates.length >= 5) {
        alert('최대 5개까지 템플릿을 선택할 수 있습니다.');
        return;
    }
    
    // 템플릿 복사본 저장 (원본 참조 문제 방지)
    selectedTemplates.push({...template});
    
    // UI 업데이트
    updateSelectedTemplatesUI();
}

/**
 * 선택된 템플릿 제거 함수
 * @param {string} templateId - 제거할 템플릿 ID
 */
function removeSelectedTemplate(templateId) {
    selectedTemplates = selectedTemplates.filter(template => template.id !== templateId);
    
    // 검색 결과에서도 체크박스 업데이트
    const checkbox = document.querySelector(`.template-checkbox[data-template-id="${templateId}"]`);
    if (checkbox) {
        checkbox.checked = false;
        const customCheckbox = checkbox.nextElementSibling;
        const checkIcon = customCheckbox.querySelector('.fa-check');
        if (customCheckbox) customCheckbox.classList.remove('bg-primary', 'checked');
        if (checkIcon) checkIcon.classList.add('opacity-0');
        
        // 카드 선택 상태 제거
        const card = checkbox.closest('.template-card') || checkbox.closest('[data-template-id]');
        if (card) card.classList.remove('selected');
    }
    
    // UI 업데이트
    updateSelectedTemplatesUI();
}

/**
 * 선택된 템플릿 UI 업데이트 함수
 */
function updateSelectedTemplatesUI() {
    const selectedContainer = document.getElementById('selected-templates-container');
    const selectedCount = document.getElementById('selected-count');
    const selectedList = document.getElementById('selected-templates');
    const generateReportBtn = document.getElementById('generate-report-btn');
    
    if (selectedTemplates.length > 0) {
        selectedContainer.classList.remove('hidden');
        selectedCount.textContent = selectedTemplates.length;
        selectedList.innerHTML = '';
        
        // 선택된 템플릿 표시
        selectedTemplates.forEach(template => {
            const item = document.createElement('div');
            item.className = 'bg-muted p-3 rounded-lg flex items-start justify-between theme-transition';
            item.innerHTML = `
                <div class="flex-grow pr-2">
                    <div class="flex items-center mb-1">
                        <span class="badge badge-primary mr-2 theme-transition">${template.docType || '문서'}</span>
                        <h4 class="text-sm font-medium text-card-foreground line-clamp-1">${template.title || '제목 없음'}</h4>
                    </div>
                    <p class="text-xs text-muted-foreground line-clamp-1">${template.ministry || '부처 정보 없음'} (${template.date ? new Date(template.date).toLocaleDateString('ko-KR') : '날짜 정보 없음'})</p>
                </div>
                <button class="remove-template-btn text-muted-foreground hover:text-destructive transition-colors" data-template-id="${template.id}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            // 삭제 버튼 이벤트
            const removeBtn = item.querySelector('.remove-template-btn');
            removeBtn.addEventListener('click', function() {
                removeSelectedTemplate(template.id);
            });
            
            selectedList.appendChild(item);
        });
        
        // 보고서 생성 버튼 활성화
        generateReportBtn.disabled = false;
    } else {
        selectedContainer.classList.add('hidden');
        selectedCount.textContent = '0';
        selectedList.innerHTML = '';
        
        // 보고서 생성 버튼 비활성화
        generateReportBtn.disabled = true;
    }
}

/**
 * 템플릿 상세 정보 표시 함수
 * @param {Object} template - 템플릿 객체
 */
function showTemplateDetail(template) {
    const templateModal = document.getElementById('template-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    
    // 모달 내용 설정
    modalTitle.textContent = template.title || '제목 없음';
    
    const date = template.date
        ? new Date(template.date).toLocaleDateString('ko-KR')
        : '날짜 정보 없음';
    
    // 문서 유형 확인 (API에서 반환하는 docType 사용)
    const docType = template.docType || '';
    
    // 문서 유형별 메타 정보 구성
    let infoHTML = '';
    
    if (docType.includes('보도자료')) {
        infoHTML = `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">발행 부처</dt>
                <dd class="text-sm text-card-foreground">${template.ministry || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">발행 부서</dt>
                <dd class="text-sm text-card-foreground">${template.department || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">담당자</dt>
                <dd class="text-sm text-card-foreground">${template.manager || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">보도일자</dt>
                <dd class="text-sm text-card-foreground">${date}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">보도시점</dt>
                <dd class="text-sm text-card-foreground">${template.time || '정보 없음'}</dd>
            </div>
        `;
    } else if (docType.includes('연설문')) {
        infoHTML = `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">연설자</dt>
                <dd class="text-sm text-card-foreground">${template.person || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">연설 장소</dt>
                <dd class="text-sm text-card-foreground">${template.place || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">연설일</dt>
                <dd class="text-sm text-card-foreground">${date}</dd>
            </div>
        `;
    } else if (docType.includes('발간사')) {
        infoHTML = `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">작성자</dt>
                <dd class="text-sm text-card-foreground">${template.person || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">발간일</dt>
                <dd class="text-sm text-card-foreground">${date}</dd>
            </div>
        `;
    } else if (docType.includes('정책보고서')) {
        infoHTML = `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">발행 부처</dt>
                <dd class="text-sm text-card-foreground">${template.ministry || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">발행 부서</dt>
                <dd class="text-sm text-card-foreground">${template.department || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">담당자</dt>
                <dd class="text-sm text-card-foreground">${template.manager || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">작성일</dt>
                <dd class="text-sm text-card-foreground">${date}</dd>
            </div>
        `;
    } else if (docType.includes('회의') || docType.includes('행사계획')) {
        infoHTML = `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">일자</dt>
                <dd class="text-sm text-card-foreground">${date}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">장소</dt>
                <dd class="text-sm text-card-foreground">${template.place || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">참석자</dt>
                <dd class="text-sm text-card-foreground">${template.person || '정보 없음'}</dd>
            </div>
        `;
    } else {
        // 기본 정보 표시
        infoHTML = `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">문서 유형</dt>
                <dd class="text-sm text-card-foreground">${docType || '정보 없음'}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">날짜</dt>
                <dd class="text-sm text-card-foreground">${date}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-muted-foreground">문서 ID</dt>
                <dd class="text-sm text-card-foreground">${template.id || '정보 없음'}</dd>
            </div>
        `;
    }
    
    // 공통 정보 추가
    infoHTML += `
        <div>
            <dt class="text-sm font-medium text-muted-foreground">문서 ID</dt>
            <dd class="text-sm text-card-foreground">${template.id || '정보 없음'}</dd>
        </div>
    `;
    
    // 모달 내용 설정 및 애니메이션 적용
    modalContent.innerHTML = `
        <div class="space-y-6 fade-in">
            <div class="flex items-center space-x-2">
                <span class="badge badge-primary">${docType || '문서'}</span>
                <span class="text-muted-foreground">${date}</span>
            </div>
            
            <div class="border-t border-border pt-4 fade-in" style="animation-delay: 0.1s;">
                <h3 class="text-lg font-medium text-card-foreground mb-4">문서 정보</h3>
                <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3 bg-muted p-4 rounded-lg theme-transition">
                    ${infoHTML}
                </dl>
            </div>
            
            <div class="border-t border-border pt-4 fade-in" style="animation-delay: 0.2s;">
                <h3 class="text-lg font-medium text-card-foreground mb-4">내용</h3>
                <div class="prose max-w-none text-sm content-area bg-muted/50 p-4 rounded-lg theme-transition">
                    ${formatContent(template.content || template.description || '내용 정보가 없습니다.')}
                </div>
            </div>
        </div>
    `;
    
    // 모달 표시 애니메이션
    templateModal.style.opacity = '0';
    templateModal.classList.remove('hidden');
    
    // 모달 페이드 인 효과
    setTimeout(() => {
        templateModal.style.opacity = '1';
        templateModal.style.transition = 'opacity 0.3s ease-in-out';
    }, 10);
}

/**
 * 내용의 줄바꿈과 포맷을 처리하는 함수
 * @param {string} content - 포맷팅할 내용
 * @returns {string} - 포맷팅된 내용
 */
function formatContent(content) {
    if (!content) return '';
    
    // HTML 콘텐츠인지 확인
    const containsHTML = /<[a-z][\s\S]*>/i.test(content);
    
    if (containsHTML) {
        // HTML이 포함된 경우 줄바꿈 및 형식 유지
        let formattedContent = content;
        
        // 빈 줄 제거 및 단락 처리
        formattedContent = formattedContent.replace(/<p>\s*<\/p>/g, '');
        
        return formattedContent;
    } else {
        // 일반 텍스트인 경우 줄바꿈 처리
        return content.split('\n').map(line => {
            // 빈 줄이면 <br> 추가
            return line.trim() === '' ? '<br>' : `<p>${line}</p>`;
        }).join('');
    }
} 