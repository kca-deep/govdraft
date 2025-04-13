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
        
        // 상세보기 이벤트 핸들러 함수
        function handleShowDetails() {
            selectedTemplate = template; // 전역 변수 업데이트 (필요시)
            showTemplateDetail(template);
        }

        // 템플릿 상세보기 이벤트 연결 (버튼 및 제목)
        const viewButton = cardElement.querySelector('.view-template-btn');
        const titleElement = cardElement.querySelector('h3');
        viewButton.addEventListener('click', handleShowDetails);
        titleElement.addEventListener('click', handleShowDetails);
        
        // 템플릿 선택 이벤트
        const checkbox = cardElement.querySelector('.template-checkbox');
        const checkboxCustom = cardElement.querySelector('.checkbox-custom'); // 스타일 업데이트에 필요
        
        // 체크박스 스타일 업데이트 함수
        function updateCheckboxStyle(isChecked) {
            const checkIcon = checkboxCustom.querySelector('.fa-check'); // 함수 내에서 찾기
            if (isChecked) {
                checkboxCustom.classList.add('bg-primary', 'checked');
                if (checkIcon) checkIcon.classList.remove('opacity-0');
                cardElement.classList.add('selected');
            } else {
                checkboxCustom.classList.remove('bg-primary', 'checked');
                if (checkIcon) checkIcon.classList.add('opacity-0');
                cardElement.classList.remove('selected');
            }
        }

        checkbox.addEventListener('change', function() {
            if (checkbox.checked) {
                if (selectedTemplates.length >= 5) {
                    checkbox.checked = false; // 상태 변경 시도 취소
                    alert('최대 5개까지 템플릿을 선택할 수 있습니다.');
                    // 스타일 변경 없이 종료
                    return;
                }
                updateCheckboxStyle(true);
                addSelectedTemplate(template);
            } else {
                updateCheckboxStyle(false);
                removeSelectedTemplate(template.id);
            }
        });
        
        // 초기 로드 시 선택된 템플릿 스타일 적용
        updateCheckboxStyle(isSelected);
        
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
    
    // 문서 유형별 메타 정보 필드 정의
    const metaFieldsConfig = {
        '보도자료': [
            { label: '발행 부처', key: 'ministry' },
            { label: '발행 부서', key: 'department' },
            { label: '담당자', key: 'manager' },
            { label: '보도일자', key: 'date', isDate: true }, // 날짜 형식 적용 플래그
            { label: '보도시점', key: 'time' }
        ],
        '연설문': [
            { label: '연설자', key: 'person' },
            { label: '연설 장소', key: 'place' },
            { label: '연설일', key: 'date', isDate: true }
        ],
        '발간사': [
            { label: '작성자', key: 'person' },
            { label: '발간일', key: 'date', isDate: true }
        ],
        '정책보고서': [
            { label: '발행 부처', key: 'ministry' },
            { label: '발행 부서', key: 'department' },
            { label: '담당자', key: 'manager' },
            { label: '작성일', key: 'date', isDate: true }
        ],
        '회의': [ // '회의/행사계획'을 포함
            { label: '일자', key: 'date', isDate: true },
            { label: '장소', key: 'place' },
            { label: '참석자', key: 'person' }
        ],
        '행사계획': [ // '회의/행사계획'을 포함
            { label: '일자', key: 'date', isDate: true },
            { label: '장소', key: 'place' },
            { label: '참석자', key: 'person' }
        ],
        'default': [ // 일치하는 유형이 없을 때 기본값
            { label: '문서 유형', key: 'docType' },
            { label: '날짜', key: 'date', isDate: true },
            { label: '문서 ID', key: 'id' }
        ]
    };

    // 현재 문서 유형에 맞는 필드 설정 가져오기
    let currentFields = metaFieldsConfig['default']; // 기본값으로 시작
    for (const typeKeyword in metaFieldsConfig) {
        if (docType.includes(typeKeyword)) {
            currentFields = metaFieldsConfig[typeKeyword];
            break; // 첫 번째 일치하는 유형 사용
        }
    }

    // infoHTML 생성
    let infoHTML = currentFields.map(field => {
        let value = template[field.key] || '정보 없음';
        if (field.isDate && value !== '정보 없음') {
            value = date; // 미리 계산된 날짜 형식 사용
        }
        return `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">${field.label}</dt>
                <dd class="text-sm text-card-foreground">${value}</dd>
            </div>
        `;
    }).join('');

    // 공통 정보인 문서 ID 추가 (currentFields에 이미 포함되지 않았다면)
    if (!currentFields.some(field => field.key === 'id')) {
        infoHTML += `
            <div>
                <dt class="text-sm font-medium text-muted-foreground">문서 ID</dt>
                <dd class="text-sm text-card-foreground">${template.id || '정보 없음'}</dd>
            </div>
        `;
    }
    
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
                <div class="max-w-none text-sm content-area bg-muted/50 p-4 rounded-lg theme-transition text-card-foreground">
                    ${formatContent(template.content || template.description || '내용 정보가 없습니다.')}
                </div>
            </div>
        </div>
    `;
    
    // 모달 표시 애니메이션
    templateModal.style.opacity = '0';
    templateModal.classList.remove('hidden');
    document.body.classList.add('modal-open'); // 모달 열 때 body 스크롤 방지
    
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