
document.addEventListener('DOMContentLoaded', function() {

    initChoicesJS();

    const searchInput = document.getElementById('searchInput');
    const semesterFilter = document.getElementById('semesterFilter');
    const cards = document.querySelectorAll('.course-card');
    const emptyState = document.getElementById('emptyState');


    function filterCourses() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        let semesterValue = 'all';
        
        if (semesterFilter) {
            if (semesterFilter._choicesInstance) {
                semesterValue = semesterFilter._choicesInstance.getValue(true) || 'all';
            } else {
                semesterValue = semesterFilter.value || 'all';
            }
        }
        
        let visible = 0;

        cards.forEach(card => {
            const code = (card.dataset.courseCode || '').toLowerCase();
            const name = (card.querySelector('.course-name')?.textContent || '').toLowerCase();
            const semester = card.dataset.semester || '';
            
            const matchSearch = !query || code.includes(query) || name.includes(query);
            const matchSemester = semesterValue === 'all' || semester === semesterValue;

            if (matchSearch && matchSemester) {
                card.style.display = '';
                visible++;
            } else {
                card.style.display = 'none';
            }
        });

        // Show empty state
        if (visible === 0) {
            emptyState.style.display = 'block';
            const btn = emptyState.querySelector('.btn-empty');
            if (query) {
                emptyState.querySelector('h3').textContent = 'No courses found';
                emptyState.querySelector('p').textContent = `No courses match "${query}"`;
                if (btn) btn.style.display = 'none';
            } else if (semesterValue !== 'all') {
                emptyState.querySelector('h3').textContent = 'No courses for this semester';
                emptyState.querySelector('p').textContent = 'You are not enrolled in any courses for the selected semester.';
                if (btn) {
                    btn.style.display = 'inline-block';
                    btn.textContent = 'View All Semesters';
                    btn.onclick = function(e) {
                        e.preventDefault();
                        if (semesterFilter._choicesInstance) {
                            semesterFilter._choicesInstance.setChoiceByValue('all');
                        } else {
                            semesterFilter.value = 'all';
                        }
                        filterCourses();
                    };
                }
            } else {
                emptyState.querySelector('h3').textContent = 'No Courses Enrolled';
                emptyState.querySelector('p').textContent = 'You are not enrolled in any courses.';
                if (btn) {
                    btn.style.display = 'inline-block';
                    btn.textContent = 'Browse Courses';
                    btn.onclick = function(e) {
                        e.preventDefault();
                        window.location.href = '/courses/browse/';
                    };
                }
            }
        } else {
            emptyState.style.display = 'none';
        }
    }

    // ---------- SEARCH INPUT ----------
    if (searchInput) {
        searchInput.addEventListener('input', filterCourses);
    }

    // ---------- SEMESTER FILTER ----------
    if (semesterFilter) {
        semesterFilter.addEventListener('change', filterCourses);
    }

    // ---------- VIEW DETAILS ----------
    document.querySelectorAll('.btn-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const card = this.closest('.course-card');
            const code = card?.dataset?.courseCode || 'course';
            const name = card?.querySelector('.course-name')?.textContent || '';
            alert(`📚 Viewing details for ${code} - ${name}`);
        });
    });

    // ---------- ACTION BUTTONS ----------
    document.querySelectorAll('.btn-icon-sm').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.course-card');
            const code = card?.dataset?.courseCode || 'course';
            const icon = this.querySelector('.ti');
            const action = icon?.className?.includes('chevron-right') ? 'View Details' : 'More Options';
            alert(`${action} for ${code}`);
        });
    });

    console.log('My Courses loaded with Choices.js');
});



function initChoicesJS() {
    const select = document.getElementById('semesterFilter');
    if (!select) return;
    
    if (typeof Choices === 'undefined') {
        console.log('Choices.js not loaded, retrying...');
        setTimeout(initChoicesJS, 500);
        return;
    }
    
    try {
        if (select._choicesInstance) {
            select._choicesInstance.destroy();
            delete select._choicesInstance;
        }
        
        const choices = new Choices(select, {
            searchEnabled: true,
            searchPlaceholderValue: 'Search semester...',
            shouldSort: false,
            position: 'auto',
            placeholder: true,
            placeholderValue: 'All Semesters',
            itemSelectText: '',
            renderSelectedChoices: 'always',
            classNames: {
                containerOuter: 'choices choices-filter',
                containerInner: 'choices__inner',
                input: 'choices__input',
                inputCloned: 'choices__input--cloned',
                list: 'choices__list',
                listItems: 'choices__list--multiple',
                listSingle: 'choices__list--single',
                listDropdown: 'choices__list--dropdown',
                item: 'choices__item',
                itemSelectable: 'choices__item--selectable',
                itemDisabled: 'choices__item--disabled',
                itemChoice: 'choices__item--choice',
                placeholder: 'choices__placeholder',
                group: 'choices__group',
                groupHeading: 'choices__heading',
                button: 'choices__button',
                activeState: 'is-active',
                focusState: 'is-focused',
                openState: 'is-open',
                disabledState: 'is-disabled',
                highlightedState: 'is-highlighted',
                hiddenState: 'is-hidden',
                flippedState: 'is-flipped',
                loadingState: 'is-loading',
                noResults: 'has-no-results',
                noChoices: 'has-no-choices'
            }
        });
        
        select._choicesInstance = choices;
        console.log(' Choices.js initialized for semester filter');
        
    } catch (e) {
        console.log(' Error initializing Choices.js:', e);
    }
}

// Expose to global
window.initChoicesJS = initChoicesJS;

console.log('My Courses JavaScript loaded');
console.log(' Fully responsive from 170px to desktop');



document.addEventListener("DOMContentLoaded", function () {

    const courseCards = document.querySelectorAll(".course-card");

    courseCards.forEach(function (card) {

        const header = card.querySelector(".card-header");

        if (!header) return;

        // =============================================
        // OPEN / CLOSE ACCORDION
        // =============================================

        header.addEventListener("click", function () {

            const isActive = card.classList.contains("active");

            // Close all other accordions
            courseCards.forEach(function (otherCard) {

                if (otherCard !== card) {

                    otherCard.classList.remove("active");

                    const otherHeader =
                        otherCard.querySelector(".card-header");

                    if (otherHeader) {

                        otherHeader.setAttribute(
                            "aria-expanded",
                            "false"
                        );

                    }
                }
            });

            // Toggle current accordion
            if (isActive) {

                card.classList.remove("active");

                header.setAttribute(
                    "aria-expanded",
                    "false"
                );

            } else {

                card.classList.add("active");

                header.setAttribute(
                    "aria-expanded",
                    "true"
                );

            }

        });


        // =============================================
        // KEYBOARD SUPPORT
        // ENTER / SPACE
        // =============================================

        header.addEventListener("keydown", function (event) {

            if (
                event.key === "Enter" ||
                event.key === " "
            ) {

                event.preventDefault();

                header.click();

            }

        });

    });

});