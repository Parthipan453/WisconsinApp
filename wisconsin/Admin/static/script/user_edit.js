// /* kali's  code  */

document.addEventListener('DOMContentLoaded', () => {

  if (window.AOS) {
    AOS.init({
      duration: 550,
      easing: 'ease-out-cubic',
      once: true,
      offset: 30,
      disable: () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
    });
  }

    let roleChoices = null;
  let userTypeChoices = null;

  if (window.Choices) {
        
        const choicesConfig = {
            searchEnabled: false,
            itemSelectText: '',
            shouldSort: false,
            position: 'bottom', 
            placeholder: false,
            renderSelectedChoices: 'always'
        };

       
        new Choices('#ue-gender', choicesConfig);
        roleChoices = new Choices('#ue-role', choicesConfig);

        userTypeChoices = new Choices('#ue-user-type', {
            ...choicesConfig,
            searchEnabled: false
        });
       
        new Choices('#ue-status', choicesConfig);
    }


    const userTypeSelect = document.getElementById('ue-user-type');
const roleSelect = document.getElementById('ue-role');

const originalRoles = [...roleSelect.options].map(option => ({
    value: option.value,
    label: option.text,
    userType: option.dataset.userType || '',
    selected: option.selected
}));

function filterRolesByUserType(userType) {

    roleChoices.clearStore();

    const filteredRoles = originalRoles.filter(role =>
        !role.value || role.userType === userType
    );

    roleChoices.setChoices(
        filteredRoles.map(role => ({
            value: role.value,
            label: role.label,
            selected: role.selected
        })),
        'value',
        'label',
        true
    );
}

userTypeSelect.addEventListener('change', function () {

    filterRolesByUserType(this.value);

    roleChoices.setChoiceByValue('');
});

filterRolesByUserType(userTypeSelect.value);




  const form          = document.getElementById('ue-form');
  const photoInput     = document.getElementById('ue-photo-input');
  const avatarPreview  = document.getElementById('ue-avatar-preview');
  const avatarNameEl   = document.getElementById('ue-avatar-name');
  const cancelBtn      = document.getElementById('ue-cancel');
  const updateBtn      = document.getElementById('ue-update');
  const updateLabel    = updateBtn.querySelector('.ue-btn__label');
  const updateSpinner  = updateBtn.querySelector('.ue-btn__spinner');

  const firstNameInput = document.getElementById('ue-first-name');
  const lastNameInput  = document.getElementById('ue-last-name');
  const usernameInput  = document.getElementById('ue-username');
  const emailInput     = document.getElementById('ue-email');

  let isDirty = false;
  form.addEventListener('input', () => { isDirty = true; });

  function syncAvatarName() {
    const full = `${firstNameInput.value} ${lastNameInput.value}`.trim();
    avatarNameEl.textContent = full || usernameInput.value || 'Unnamed user';
  }
  firstNameInput.addEventListener('input', syncAvatarName);
  lastNameInput.addEventListener('input', syncAvatarName);

  photoInput.addEventListener('change', () => {
    const file = photoInput.files[0];
    if (!file) return;
    isDirty = true;
    const reader = new FileReader();
    reader.onload = (e) => {
      avatarPreview.innerHTML = `<img src="${e.target.result}" alt="" id="ue-avatar-img">`;
    };
    reader.readAsDataURL(file);
  });

  function setFieldError(field, message) {
    const wrap = field.closest('.ue-field');
    wrap.classList.add('ue-field--error');
    let msg = wrap.querySelector('.ue-error-msg');
    if (!msg) {
      msg = document.createElement('span');
      msg.className = 'ue-error-msg';
      wrap.appendChild(msg);
    }
    msg.textContent = message;
  }

  function clearFieldError(field) {
    const wrap = field.closest('.ue-field');
    wrap.classList.remove('ue-field--error');
    const msg = wrap.querySelector('.ue-error-msg');
    if (msg) msg.remove();
  }

  function validate() {
    let valid = true;
    [firstNameInput, usernameInput, emailInput].forEach(clearFieldError);

    if (!firstNameInput.value.trim()) {
      setFieldError(firstNameInput, 'First name is required');
      valid = false;
    }
    if (!usernameInput.value.trim()) {
      setFieldError(usernameInput, 'Username is required');
      valid = false;
    }
    const emailVal = emailInput.value.trim();
    if (!emailVal) {
      setFieldError(emailInput, 'Email is required');
      valid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
      setFieldError(emailInput, 'Enter a valid email address');
      valid = false;
    }
    return valid;
  }

  function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `ue-toast ue-toast--${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('ue-toast--show'));
    setTimeout(() => {
      toast.classList.remove('ue-toast--show');
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

  function setLoading(isLoading) {
    updateBtn.disabled = isLoading;
    updateSpinner.hidden = !isLoading;
    updateLabel.textContent = isLoading ? 'Updating…' : 'Update User';
  }

  cancelBtn.addEventListener('click', () => {
    if (isDirty && !window.confirm('Discard unsaved changes?')) return;
    window.location.href = UE_CONFIG.usersUrl;
  });

  window.addEventListener('beforeunload', (e) => {
    if (isDirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!validate()) {
      showToast('Please fix the highlighted fields', 'error');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData(form);
      const res = await fetch(UE_CONFIG.updateUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
      });

      let data = {};
      try { data = await res.json(); } catch (_) { }

      if (res.ok && data.ok) {
        isDirty = false;
        sessionStorage.setItem('ub_toast', JSON.stringify({
          type: 'success',
          message: 'User updated successfully!'
        }));
        window.location.href = UE_CONFIG.usersUrl;
        return;
      }

      let message = 'Could not update user. Please check the form.';
      if (data.errors) {
        const firstKey = Object.keys(data.errors)[0];
        const firstVal = data.errors[firstKey];
        message = Array.isArray(firstVal) ? firstVal[0] : String(firstVal);
      }
      showToast(message, 'error');
      setLoading(false);

    } catch (err) {
      showToast('Network error — please try again.', 'error');
      setLoading(false);
    }
  });
  

});