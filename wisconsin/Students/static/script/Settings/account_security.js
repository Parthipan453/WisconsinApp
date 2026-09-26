// static/script/Settings/account_security.js

/* ============================================================
   DOM Ready
   ============================================================ */
document.addEventListener('DOMContentLoaded', function() {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 300,
            once: true
        });
    }
    checkPasswordMatch();
    updateSecurityScore();
});

/* ============================================================
   Password Management
   ============================================================ */

function checkPasswordStrength(password) {
    const strengthFill = document.getElementById('strengthFill');
    const requirements = {
        length: document.getElementById('reqLength'),
        upper: document.getElementById('reqUpper'),
        lower: document.getElementById('reqLower'),
        digit: document.getElementById('reqDigit'),
        special: document.getElementById('reqSpecial')
    };

    if (!strengthFill) return;

    // Check requirements
    const hasLength = password.length >= 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasDigit = /\d/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    // Update requirements UI
    updateRequirement(requirements.length, hasLength);
    updateRequirement(requirements.upper, hasUpper);
    updateRequirement(requirements.lower, hasLower);
    updateRequirement(requirements.digit, hasDigit);
    updateRequirement(requirements.special, hasSpecial);

    // Calculate strength
    let score = 0;
    if (hasLength) score++;
    if (hasUpper) score++;
    if (hasLower) score++;
    if (hasDigit) score++;
    if (hasSpecial) score++;

    let className;
    if (score <= 1) className = 'weak';
    else if (score <= 2) className = 'fair';
    else if (score <= 3) className = 'good';
    else className = 'strong';

    strengthFill.className = 'strength-fill ' + className;
    
    // Update security score
    updateSecurityScore();
}

function updateRequirement(element, met) {
    if (element) {
        if (met) {
            element.classList.add('met');
        } else {
            element.classList.remove('met');
        }
    }
}

function checkPasswordMatch() {
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    const matchHint = document.getElementById('matchHint');

    if (!newPassword || !confirmPassword || !matchHint) return;

    if (confirmPassword.value.length === 0) {
        matchHint.classList.remove('visible', 'mismatch');
        return;
    }

    if (newPassword.value === confirmPassword.value) {
        matchHint.textContent = '✓ Passwords match';
        matchHint.className = 'sec-match-hint visible';
    } else {
        matchHint.textContent = '✗ Passwords do not match';
        matchHint.className = 'sec-match-hint visible mismatch';
    }
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(inputId + 'Icon');

    if (input && icon) {
        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'ti ti-eye-off';
        } else {
            input.type = 'password';
            icon.className = 'ti ti-eye';
        }
    }
}

/* ============================================================
   Security Score
   ============================================================ */

function updateSecurityScore() {
    const scoreElement = document.getElementById('securityScore');
    if (!scoreElement) return;

    let score = 85; // Base score
    
    // Check password strength
    const newPassword = document.getElementById('newPassword');
    if (newPassword && newPassword.value.length > 0) {
        const strength = getPasswordStrength(newPassword.value);
        if (strength === 'strong') score += 10;
        else if (strength === 'good') score += 5;
        else if (strength === 'weak') score -= 10;
    }
    
    // Check 2FA
    const twofaStatus = document.getElementById('twofaStatus');
    if (twofaStatus && twofaStatus.classList.contains('enabled')) {
        score += 5;
    } else {
        score -= 5;
    }
    
    // Clamp score
    score = Math.max(0, Math.min(100, score));
    scoreElement.textContent = score;
}

function getPasswordStrength(password) {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;
    
    if (score <= 1) return 'weak';
    if (score <= 2) return 'fair';
    if (score <= 3) return 'good';
    return 'strong';
}

/* ============================================================
   Password Form Submission (AJAX)
   ============================================================ */

document.addEventListener('DOMContentLoaded', function() {
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const currentPassword = document.getElementById('currentPassword');
            const newPassword = document.getElementById('newPassword');
            const confirmPassword = document.getElementById('confirmPassword');

            // Validate
            if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
                toastError('All fields are required');  // ✅ Parent toast
                return;
            }

            if (newPassword.value !== confirmPassword.value) {
                toastError('Passwords do not match');  // ✅ Parent toast
                return;
            }

            if (newPassword.value.length < 8) {
                toastError('Password must be at least 8 characters');  // ✅ Parent toast
                return;
            }

            // Show loading state
            const submitBtn = document.getElementById('updatePasswordBtn');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="ti ti-loader spin"></i> Updating...';
            submitBtn.disabled = true;

            // Submit via AJAX
            const formData = new FormData(this);

            fetch('/student/settings/security/change-password-ajax/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastSuccess(data.message || 'Password updated successfully!');  // ✅ Parent toast
                    currentPassword.value = '';
                    newPassword.value = '';
                    confirmPassword.value = '';
                    document.getElementById('strengthFill').className = 'strength-fill';
                    document.getElementById('matchHint').classList.remove('visible', 'mismatch');
                    document.querySelectorAll('.sec-pwd-requirements li').forEach(el => {
                        el.classList.remove('met');
                    });
                    updateSecurityScore();
                } else {
                    toastError(data.message || 'Failed to update password');  // ✅ Parent toast
                }
            })
            .catch(() => {
                toastError('Network error. Please try again.');  // ✅ Parent toast
            })
            .finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    }
});

/* ============================================================
   Two-Factor Authentication
   ============================================================ */

function toggle2FA() {
    const statusElement = document.getElementById('twofaStatus');
    const isEnabled = statusElement && statusElement.classList.contains('enabled');
    const modal = document.getElementById('twofaModal');
    
    if (!modal) return;
    
    const title = modal.querySelector('.sec-modal-header h2');
    const content = document.getElementById('twofaSetupContent');
    const confirmBtn = document.getElementById('twofaConfirmBtn');

    if (isEnabled) {
        if (title) title.innerHTML = '<i class="ti ti-shield-off"></i> Disable 2FA';
        if (content) {
            content.innerHTML = `
                <div class="twofa-disable">
                    <p style="font-size:13px;color:#666;">Are you sure you want to disable two-factor authentication? This will make your account less secure.</p>
                    <p style="font-size:13px;color:#666;margin-top:10px;">Enter your password to confirm:</p>
                    <input type="password" class="sec-input-wrap" id="confirmPassword2FA" placeholder="Enter your password" style="width:100%;height:40px;border:1.5px solid #e8e8e8;border-radius:8px;padding:0 12px;font-size:13px;margin-top:4px;">
                </div>
            `;
        }
        if (confirmBtn) confirmBtn.textContent = 'Disable 2FA';
    } else {
        if (title) title.innerHTML = '<i class="ti ti-shield-plus"></i> Enable 2FA';
        if (content) {
            content.innerHTML = `
                <div class="twofa-setup">
                    <p style="font-size:13px;color:#666;">Scan the QR code below with your authenticator app (Google Authenticator, Authy, etc.)</p>
                    <div style="display:flex;justify-content:center;padding:12px 0;">
                        <div id="qrPlaceholder" style="width:140px;height:140px;background:#f8f8f8;border:2px dashed #ddd;border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#999;font-size:12px;gap:4px;">
                            <i class="ti ti-qrcode" style="font-size:36px;"></i>
                            <span>Loading...</span>
                        </div>
                    </div>
                    <div class="secret-key" style="margin:8px 0;">
                        <label style="font-size:11px;font-weight:600;color:#666;">Secret Key</label>
                        <div style="display:flex;align-items:center;gap:8px;background:#f5f5f5;padding:6px 10px;border-radius:6px;font-family:monospace;font-size:12px;letter-spacing:1px;margin-top:2px;">
                            <span id="secretKey">Loading...</span>
                            <button class="sec-btn-secondary" onclick="copySecretKey()" style="padding:2px 8px;font-size:10px;margin-left:auto;">
                                <i class="ti ti-copy"></i> Copy
                            </button>
                        </div>
                    </div>
                    <div class="verification-code" style="margin-top:8px;">
                        <label style="font-size:11px;font-weight:600;color:#666;">Enter 6-digit code to verify</label>
                        <input type="text" id="verificationCode" placeholder="123456" maxlength="6" style="width:100%;height:40px;border:1.5px solid #e8e8e8;border-radius:8px;padding:0 12px;font-size:18px;text-align:center;letter-spacing:4px;margin-top:2px;">
                    </div>
                </div>
            `;
        }
        if (confirmBtn) confirmBtn.textContent = 'Enable 2FA';
        // Generate QR code and secret key
        generate2FASetup();
    }

    modal.classList.add('open');
}

function generate2FASetup() {
    fetch('/student/settings/security/2fa/setup-ajax/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const secretKey = document.getElementById('secretKey');
            const qrPlaceholder = document.getElementById('qrPlaceholder');
            
            if (secretKey) secretKey.textContent = data.secret_key;
            
            if (qrPlaceholder && data.qr_code) {
                qrPlaceholder.innerHTML = `<img src="${data.qr_code}" alt="QR Code" style="max-width:100%;max-height:100%;">`;
            }
        } else {
            toastError(data.message || 'Failed to generate 2FA setup');  // ✅ Parent toast
        }
    })
    .catch(() => {
        toastError('Network error. Please try again.');  // ✅ Parent toast
    });
}

function confirm2FASetup() {
    const statusElement = document.getElementById('twofaStatus');
    const isEnabled = statusElement && statusElement.classList.contains('enabled');

    if (isEnabled) {
        const passwordInput = document.getElementById('confirmPassword2FA');
        if (!passwordInput || !passwordInput.value) {
            toastError('Please enter your password');  // ✅ Parent toast
            return;
        }

        const data = { password: passwordInput.value };

        fetch('/student/settings/security/2fa/disable-ajax/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastSuccess(data.message || '2FA disabled successfully');  // ✅ Parent toast
                closeModal('twofaModal');
                location.reload();
            } else {
                toastError(data.message || 'Failed to disable 2FA');  // ✅ Parent toast
            }
        })
        .catch(() => {
            toastError('Network error. Please try again.');  // ✅ Parent toast
        });
    } else {
        const codeInput = document.getElementById('verificationCode');
        if (!codeInput || !codeInput.value || codeInput.value.length !== 6) {
            toastError('Please enter a valid 6-digit code');  // ✅ Parent toast
            return;
        }

        const data = { code: codeInput.value };

        fetch('/student/settings/security/2fa/verify-ajax/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastSuccess(data.message || '2FA enabled successfully!');  // ✅ Parent toast
                closeModal('twofaModal');
                location.reload();
            } else {
                toastError(data.message || 'Invalid verification code');  // ✅ Parent toast
            }
        })
        .catch(() => {
            toastError('Network error. Please try again.');  // ✅ Parent toast
        });
    }
}

function showBackupCodes() {
    const modal = document.getElementById('backupCodesModal');
    if (!modal) return;
    
    modal.classList.add('open');

    fetch('/student/settings/security/2fa/backup-codes-ajax/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.codes) {
            const container = document.getElementById('backupCodesContainer');
            if (container) {
                container.innerHTML = data.codes.map(code =>
                    `<div class="backup-code">${code}</div>`
                ).join('');
            }
        } else {
            toastError(data.message || 'Failed to fetch backup codes');  // ✅ Parent toast
        }
    })
    .catch(() => {
        toastError('Network error. Please try again.');  // ✅ Parent toast
    });
}

function copySecretKey() {
    const secretKey = document.getElementById('secretKey');
    if (!secretKey) return;
    
    navigator.clipboard.writeText(secretKey.textContent).then(() => {
        toastSuccess('Secret key copied to clipboard!');  // ✅ Parent toast
    }).catch(() => {
        toastError('Failed to copy secret key');  // ✅ Parent toast
    });
}

function downloadBackupCodes() {
    const codes = document.querySelectorAll('.backup-code');
    if (codes.length === 0) {
        toastError('No backup codes available');  // ✅ Parent toast
        return;
    }
    
    let text = 'Backup Codes\n';
    text += '='.repeat(30) + '\n\n';
    codes.forEach((code, index) => {
        text += `${index + 1}. ${code.textContent}\n`;
    });
    text += '\n' + '='.repeat(30) + '\n';
    text += 'Generated: ' + new Date().toLocaleString();

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup_codes.txt';
    a.click();
    URL.revokeObjectURL(url);
}

/* ============================================================
   Session Management
   ============================================================ */

function revokeSession(sessionKey) {
    if (!confirm('This device will be signed out immediately. Continue?')) {
        return;
    }

    const data = { session_key: sessionKey };

    fetch('/student/settings/security/sessions/revoke-ajax/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastSuccess(data.message || 'Session revoked successfully');  // ✅ Parent toast
            location.reload();
        } else {
            toastError(data.message || 'Failed to revoke session');  // ✅ Parent toast
        }
    })
    .catch(() => {
        toastError('Network error. Please try again.');  // ✅ Parent toast
    });
}

function revokeAllSessions() {
    if (!confirm('All other devices will be signed out. Continue?')) {
        return;
    }

    fetch('/student/settings/security/sessions/revoke-all-ajax/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastSuccess(data.message || 'All other sessions revoked');  // ✅ Parent toast
            location.reload();
        } else {
            toastError(data.message || 'Failed to revoke sessions');  // ✅ Parent toast
        }
    })
    .catch(() => {
        toastError('Network error. Please try again.');  // ✅ Parent toast
    });
}

/* ============================================================
   Account Deactivation
   ============================================================ */

function confirmDeactivate() {
    if (!confirm(
        '⚠️ Your account will be deactivated.\n\n' +
        'You will need to contact the Registrar to reactivate it.\n\n' +
        'Continue?'
    )) {
        return;
    }

    const password = prompt('Please enter your password to confirm deactivation:');
    if (!password) return;

    const data = { password: password };

    fetch('/student/settings/security/deactivate-ajax/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastSuccess(data.message || 'Account deactivated successfully');  // ✅ Parent toast
            setTimeout(() => {
                window.location.href = '/logout/';
            }, 1500);
        } else {
            toastError(data.message || 'Failed to deactivate account');  // ✅ Parent toast
        }
    })
    .catch(() => {
        toastError('Network error. Please try again.');  // ✅ Parent toast
    });
}

function confirmDeleteAccount() {
    if (!confirm(
        '⚠️ DANGER: This action is permanent and cannot be undone!\n\n' +
        'All your data will be permanently deleted.\n\n' +
        'Are you absolutely sure?'
    )) {
        return;
    }

    const password = prompt('Please enter your password to confirm deletion:');
    if (!password) return;

    const confirmText = prompt('Type "DELETE" to confirm permanent deletion:');
    if (confirmText !== 'DELETE') {
        toastInfo('Account deletion cancelled');  // ✅ Parent toast
        return;
    }

    const data = { password: password };

    fetch('/settings/security/delete-account-ajax/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastSuccess(data.message || 'Account deleted permanently');  // ✅ Parent toast
            setTimeout(() => {
                window.location.href = '/logout/';
            }, 1500);
        } else {
            toastError(data.message || 'Failed to delete account');  // ✅ Parent toast
        }
    })
    .catch(() => {
        toastError('Network error. Please try again.');  // ✅ Parent toast
    });
}

/* ============================================================
   Modal Management
   ============================================================ */

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('open');
}

// Close modal on overlay click
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.sec-modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('open');
            }
        });
    });
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.sec-modal-overlay.open').forEach(modal => {
            modal.classList.remove('open');
        });
    }
});

/* ============================================================
   Toast Notifications - Using Parent Toast
   ============================================================ */

// showToast function now uses parent toast
// This is kept for backward compatibility
function showToast(type, message) {
    const typeMap = {
        'success': toastSuccess,
        'error': toastError,
        'info': toastInfo,
        'warning': toastWarning
    };
    
    const func = typeMap[type] || toastInfo;
    func(message);
}

/* ============================================================
   CSRF Helper
   ============================================================ */

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
    return '';
}

/* ============================================================
   Keyboard Shortcuts
   ============================================================ */

document.addEventListener('keydown', function(e) {
    // Ctrl+Enter to submit password form
    if (e.ctrlKey && e.key === 'Enter') {
        const form = document.getElementById('passwordForm');
        if (form && document.activeElement && form.contains(document.activeElement)) {
            form.dispatchEvent(new Event('submit'));
        }
    }
});

console.log('Account Security using parent toast system!');