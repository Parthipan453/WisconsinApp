document.addEventListener("DOMContentLoaded", function () {

    // ===============================
    // Move any already-open modal to <body>
    // (e.g. the Add Member modal re-rendered open by Django
    // after a validation error). Every other modal gets this
    // treatment inside rcToggle before it's shown; this one is
    // opened by the server directly, so it skips rcToggle and
    // would otherwise stay nested wherever the template put it —
    // which can throw off position:fixed centering if any
    // ancestor in the page layout has a transform/transition on it.
    // ===============================
    document.querySelectorAll(".rc-modal-overlay").forEach(function (el) {
        const isOpen = el.style.display === "flex" || getComputedStyle(el).display === "flex";
        if (isOpen && !el.dataset.moved) {
            document.body.appendChild(el);
            el.dataset.moved = "true";
            document.body.style.overflow = "hidden";
        }
    });

    // ===============================
    // Toggle Modal
    // ===============================
    window.rcToggle = function(id) {
        const el = document.getElementById(id);
        if (!el) return;
        if (!el.dataset.moved) {
            document.body.appendChild(el);
            el.dataset.moved = "true";
        }
        if (el.style.display === "flex") {
            el.style.display = "none";
            document.body.style.overflow = "";
            const form = el.querySelector("form");
            if (form) {
                form.reset();
                form.querySelectorAll(".rc-field-error").forEach(function(error){
                    error.innerHTML = "";
                });
                form.querySelectorAll("select").forEach(function(select){
                    if(select.choices){
                        select.choices.hideDropdown();
                        select.choices.removeActiveItems();
                        select.choices.setChoiceByValue("");
                    }
                });
            }
        } else {

            el.style.display = "flex";
            document.body.style.overflow = "hidden";
        }
    };

    // ===============================
    // Close outside click
    // ===============================
    document.addEventListener("click", function(e){
        if(e.target.classList.contains("rc-modal-overlay")){
            rcToggle(e.target.id);
        }
    });

    // ===============================
    // Choices.js
    // ===============================
    const choicesInstances = new Map();
    document.querySelectorAll("select").forEach(function(select){
        const isFaculty = select.classList.contains("faculty-select");
        const choice = new Choices(select,{
            searchEnabled: isFaculty,
            itemSelectText:'',
            shouldSort:false,
            shouldSortItems:false
        });
        choicesInstances.set(select,choice);
        select.choices = choice;

    });

    // ===============================
    // Edit Form AJAX Submit
    // ===============================
    document.querySelectorAll(".rc-edit-form").forEach(function(form){
        form.addEventListener("submit",function(e){
            e.preventDefault();
            fetch(form.action,{
                method:"POST",
                body:new FormData(form),
                headers:{
                    "X-Requested-With":"XMLHttpRequest"
                }
            })
            .then(response=>response.json())
            .then(result=>{
                if(result.success){
                    window.location.reload();
                    return;
                }
                form.querySelectorAll(".rc-field-error").forEach(function(error){
                    error.innerHTML="";
                });
                Object.keys(result.errors).forEach(function(field){
                    const input=form.querySelector(`[name="${field}"]`);
                    if(input){
                        const box=input
                        .closest(".rc-form-group")
                        .querySelector(".rc-field-error");
                        if(box){
                            box.innerHTML =
                            result.errors[field][0];
                        }
                    }

                });
            });
        });
    });

    // ===============================
    // Department -> Faculty
    // ===============================
    document.querySelectorAll(".department-select").forEach(function(departmentSelect){
        departmentSelect.addEventListener("change",function(){
            const departmentId=this.value;
            const form=this.closest("form");
            const facultySelect=form.querySelector(".faculty-select");
            if(!facultySelect) return;
            const facultyChoice=choicesInstances.get(facultySelect);
            if(!facultyChoice) return;
            facultyChoice.clearStore();
            if(!departmentId){
                facultyChoice.setChoices(
                    [{
                        value:"",
                        label:"Select Faculty",
                        disabled:true
                    }],
                    "value",
                    "label",
                    true
                );
                return;
            }
            fetch(
                facultyByDepartmentUrl.replace(
                    "999999",
                    departmentId
                )
            )
            .then(res=>res.json())
            .then(data=>{
                facultyChoice.setChoices(
                    data.faculties.map(function(faculty){
                        return {
                            value:faculty.id,
                            label:faculty.name
                        };
                    }),
                    "value",
                    "label",
                    true
                );
            });
        });
    });

// ===============================
// Deactivate Confirmation Modal
// ===============================
let rcDeactivateUrl = null;

window.rcConfirmDeactivate = function (url, name) {
    rcDeactivateUrl = url;
    document.getElementById("rcDeactivateName").textContent = name;
    rcToggle("rcDeactivateModal");
};

const rcDeactivateConfirmBtn = document.getElementById("rcDeactivateConfirmBtn");
if (rcDeactivateConfirmBtn) {
    rcDeactivateConfirmBtn.addEventListener("click", function () {
        if (!rcDeactivateUrl) return;
        const form = document.getElementById("rcDeactivateForm");
        form.action = rcDeactivateUrl;
        form.submit();
    });
}    
});