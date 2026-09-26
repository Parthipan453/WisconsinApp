const TOAST_DURATION = 4000;

    const TOAST_CONFIG = {
        success: { icon: '<i class="fa-solid fa-circle-check"></i>', title: "Done" },
        error: { icon: '<i class="fa-solid fa-circle-xmark"></i>', title: "Error" },
        warning: { icon: '<i class="fa-solid fa-triangle-exclamation"></i>', title: "Warning" },
        info: { icon: '<i class="fa-solid fa-circle-info"></i>', title: "Info" },
    };

    function showToast(tag, message) {
        const container = document.getElementById("custom-toast-container")
        if (!container) {
            return;
        }

        const config = TOAST_CONFIG[tag] || TOAST_CONFIG.info;

        const toast = document.createElement("div");
        toast.className = `custom-toast custom-toast--${tag}`;
        toast.setAttribute("role", "alert");
        toast.setAttribute("aria-live", "assertive");

        const fillId = `custom-toast-fill-${Date.now()}-${Math.random()}`;

        toast.innerHTML = `
            <div class="custom-toast__body">
                <span class="custom-toast__icon" aria-hidden="true">${config.icon}</span>

                <div class="custom-toast__content">
                    <div class="custom-toast__title">${config.title}</div>
                    <div class="custom-toast__message">${message}</div>
                    <hr>
                    <div class="custom-toast__hint">
                        <i class="fa-regular fa-hand-pointer"></i>
                        This notification will stay on screen while your mouse is over it.
                    </div>
                </div>
            </div>

            <button class="custom-toast__dismiss" aria-label="Dismiss notification">
                <i class="fa-solid fa-xmark"></i>
            </button>

            <div class="custom-toast__progress">
                <div class="custom-toast__progress-fill" id="${fillId}"></div>
            </div>
        `;

        container.appendChild(toast);

        let dismissed = false;
        let autoTimer = null;
        let remainingMs = TOAST_DURATION;
        let startedAt = null;
        let isPaused = false;

        const fill = document.getElementById(fillId);

        function dismiss() {
            if (dismissed) return;
            dismissed = true;
            clearTimeout(autoTimer);
            toast.classList.remove("custom-toast--visible");
            toast.classList.add("custom-toast--dismissing");
            setTimeout(() => toast.remove(), 280);
        }

        function startTimer(durationMs) {
            clearTimeout(autoTimer);
            autoTimer = setTimeout(dismiss, durationMs);
        }

        toast.querySelector(".custom-toast__dismiss").addEventListener("click", dismiss);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                toast.classList.add("custom-toast--visible");
            });
        });

        let animation = null;

        function startBarAnimation(durationMs) {
            if (animation) {
                animation.cancel();
            }
            animation = fill.animate(
                [{ transform: "scaleX(1)" }, { transform: "scaleX(0)" }],
                { duration: durationMs, easing: "linear", fill: "forwards" }
            );
            animation.onfinish = () => {
                dismiss();
            };
        }

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                startedAt = Date.now();
                startTimer(remainingMs);
                startBarAnimation(remainingMs);
            });
        });

        toast.addEventListener("mouseenter", () => {
            if (dismissed || isPaused) return;
            isPaused = true;
            clearTimeout(autoTimer);

            if (startedAt !== null) {
                const elapsed = Date.now() - startedAt;
                remainingMs = Math.max(0, remainingMs - elapsed);
                startedAt = null;
            }

            if (animation) {
                animation.pause();
            }
        });

        toast.addEventListener("mouseleave", () => {
            if (dismissed || !isPaused) return;
            isPaused = false;

            if (remainingMs <= 0) {
                dismiss();
                return;
            }

            startedAt = Date.now();
            startTimer(remainingMs);

            if (animation) {
                animation.updatePlaybackRate(1);
                animation.play();
            }
        });
    }

    function initToasts() {
        const items = document.querySelectorAll("[data-toast-tag]");
        items.forEach((el, index) => {
            setTimeout(() => {
            showToast(el.dataset.toastTag, el.dataset.toastMessage);
            }, index * 120);
        });
    }

    initToasts()