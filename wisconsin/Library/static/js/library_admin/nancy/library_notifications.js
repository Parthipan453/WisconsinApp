(function () {
    "use strict";

    const toggle = document.getElementById("notifToggle");
    const badge = document.getElementById("notifBadge");
    const notificationSound =
        document.getElementById("libraryNotifSound");
    const dropdown = document.getElementById("notifDropdown");

    if (!toggle || !badge || !dropdown) {
        return;
    }

    /*
     * ----------------------------------------------------
     * DJANGO URLS
     * ----------------------------------------------------
     */

    const NOTIFICATION_URL =
        "/library/notifications/";

    const READ_URL_BASE =
        "/library/notifications/";

    const list =
        dropdown.querySelector(".notif__list");


    /*
     * ----------------------------------------------------
     * NOTIFICATION TRACKING
     * ----------------------------------------------------
     *
     * Used to detect a genuinely new notification.
     *
     * We don't play sound on the first page load.
     * Sound only plays when a new notification appears
     * after the dashboard has already loaded.
     */

    let latestNotificationId = null;


    /*
     * ----------------------------------------------------
     * CSRF TOKEN
     * ----------------------------------------------------
     */

    function getCookie(name) {

        const cookies = document.cookie
            .split(";")
            .map(cookie => cookie.trim());

        for (const cookie of cookies) {

            if (cookie.startsWith(name + "=")) {

                return decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
            }
        }

        return null;
    }

    const csrfToken =
        getCookie("csrftoken");


    /*
     * ----------------------------------------------------
     * PLAY NOTIFICATION SOUND
     * ----------------------------------------------------
     */

    function playNotificationSound() {

        if (!notificationSound) {
            return;
        }

        /*
         * Restart the sound if it is already playing.
         */

        notificationSound.currentTime = 0;

        notificationSound.play().catch(error => {

            /*
             * Browsers can block audio playback until
             * the user interacts with the page.
             *
             * Don't let that break notifications.
             */

            console.debug(
                "Library notification sound could not play:",
                error
            );
        });
    }


    /*
     * ----------------------------------------------------
     * FORMAT TIME
     * ----------------------------------------------------
     */

    function formatTime(dateString) {

        if (!dateString) {
            return "";
        }

        const date =
            new Date(dateString);

        if (Number.isNaN(date.getTime())) {
            return "";
        }

        const now =
            new Date();

        const difference =
            Math.floor(
                (now - date) / 1000
            );


        if (difference < 60) {
            return "Just now";
        }


        if (difference < 3600) {

            const minutes =
                Math.floor(
                    difference / 60
                );

            return `${minutes} min ago`;
        }


        if (difference < 86400) {

            const hours =
                Math.floor(
                    difference / 3600
                );

            return `${hours} hr ago`;
        }


        if (difference < 604800) {

            const days =
                Math.floor(
                    difference / 86400
                );

            return (
                `${days} day` +
                `${days > 1 ? "s" : ""} ago`
            );
        }


        return date.toLocaleDateString();
    }


    /*
     * ----------------------------------------------------
     * NOTIFICATION TYPE ICON
     * ----------------------------------------------------
     */

    function getNotificationIcon(type) {

        switch (type) {

            case "SUCCESS":
                return "circle-check";

            case "WARNING":
                return "triangle-alert";

            case "ERROR":
                return "circle-x";

            case "REQUEST":
                return "clipboard-list";

            case "SYSTEM":
                return "settings";

            case "INFO":
            default:
                return "info";
        }
    }


    /*
     * ----------------------------------------------------
     * UPDATE BADGE
     * ----------------------------------------------------
     */

    function updateBadge(count) {

        const unreadCount =
            Number(count) || 0;


        if (unreadCount > 0) {

            badge.textContent =
                unreadCount > 99
                    ? "99+"
                    : unreadCount;

            badge.style.display =
                "inline-flex";

        } else {

            badge.textContent = "0";

            badge.style.display =
                "none";
        }
    }


    /*
     * ----------------------------------------------------
     * RENDER NOTIFICATIONS
     * ----------------------------------------------------
     */

    function renderNotifications(
        notifications
    ) {

        if (!list) {
            return;
        }

        list.innerHTML = "";


        /*
         * No notifications
         */

        if (
            !notifications ||
            notifications.length === 0
        ) {

            const empty =
                document.createElement("li");

            empty.className =
                "notif__empty";

            empty.textContent =
                "No notifications";

            list.appendChild(empty);

            return;
        }


        /*
         * Render each notification
         */

        notifications.forEach(
            notification => {

                const item =
                    document.createElement("li");


                item.className =
                    "notif__item" +
                    (
                        notification.is_read
                            ? ""
                            : " notif__item--unread"
                    );


                /*
                 * ----------------------------------------
                 * ICON
                 * ----------------------------------------
                 */

                const iconWrapper =
                    document.createElement("div");

                iconWrapper.className =
                    "notif__icon notif__icon--" +
                    String(
                        notification.notification_type ||
                        "INFO"
                    ).toLowerCase();


                const icon =
                    document.createElement("i");

                icon.setAttribute(
                    "data-lucide",
                    getNotificationIcon(
                        notification.notification_type
                    )
                );


                iconWrapper.appendChild(icon);


                /*
                 * ----------------------------------------
                 * CONTENT
                 * ----------------------------------------
                 */

                const content =
                    document.createElement("div");

                content.className =
                    "notif__content";


                /*
                 * Title
                 */

                const title =
                    document.createElement("div");

                title.className =
                    "notif__title";

                title.textContent =
                    notification.title ||
                    "Notification";


                /*
                 * Message
                 */

                const message =
                    document.createElement("div");

                message.className =
                    "notif__message";

                message.textContent =
                    notification.message ||
                    "";


                /*
                 * Time
                 */

                const time =
                    document.createElement("div");

                time.className =
                    "notif__time";

                time.textContent =
                    formatTime(
                        notification.created_at
                    );


                content.appendChild(title);
                content.appendChild(message);
                content.appendChild(time);


                /*
                 * ----------------------------------------
                 * UNREAD INDICATOR
                 * ----------------------------------------
                 */

                if (!notification.is_read) {

                    const unreadDot =
                        document.createElement("span");

                    unreadDot.className =
                        "notif__unread-dot";

                    item.appendChild(
                        unreadDot
                    );
                }


                item.appendChild(
                    iconWrapper
                );

                item.appendChild(
                    content
                );


                /*
                 * ----------------------------------------
                 * CLICK NOTIFICATION
                 * ----------------------------------------
                 */

                item.addEventListener(
                    "click",
                    function () {

                        handleNotificationClick(
                            notification,
                            item
                        );
                    }
                );


                list.appendChild(item);
            }
        );


        /*
         * Re-create Lucide icons after
         * dynamically inserting them.
         */

        if (
            window.lucide &&
            typeof lucide.createIcons === "function"
        ) {

            lucide.createIcons();
        }
    }


    /*
     * ----------------------------------------------------
     * LOAD NOTIFICATIONS
     * ----------------------------------------------------
     */

    async function loadNotifications() {

        try {

            const response =
                await fetch(
                    NOTIFICATION_URL,
                    {
                        method: "GET",

                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest"
                        },

                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Notification request failed"
                );
            }


            const data =
                await response.json();


            const notifications =
                data.notifications || [];


            /*
             * --------------------------------------------
             * DETECT NEW NOTIFICATION
             * --------------------------------------------
             */

            if (notifications.length > 0) {

                /*
                 * The API returns notifications ordered
                 * newest first.
                 */

                const newestNotification =
                    notifications[0];


                const currentNotificationId =
                    newestNotification.id;


                /*
                 * First page load:
                 *
                 * Store the current notification ID
                 * but DON'T play sound.
                 */

                if (
                    latestNotificationId === null
                ) {

                    latestNotificationId =
                        currentNotificationId;

                }


                /*
                 * Later polling:
                 *
                 * If the newest notification ID has
                 * changed and the notification is unread,
                 * play the notification sound.
                 */

                else if (
                    currentNotificationId !==
                    latestNotificationId &&
                    !newestNotification.is_read
                ) {

                    playNotificationSound();

                    latestNotificationId =
                        currentNotificationId;
                }
            }


            /*
             * If there are no notifications,
             * reset the tracked ID.
             */

            else {

                latestNotificationId = null;
            }


            /*
             * --------------------------------------------
             * UPDATE BADGE
             * --------------------------------------------
             */

            updateBadge(
                data.unread_count
            );


            /*
             * --------------------------------------------
             * RENDER NOTIFICATIONS
             * --------------------------------------------
             */

            renderNotifications(
                notifications
            );


        } catch (error) {

            console.error(
                "Library notification error:",
                error
            );
        }
    }


    /*
     * ----------------------------------------------------
     * MARK AS READ
     * ----------------------------------------------------
     */

    async function markAsRead(
        notificationId
    ) {

        try {

            const response =
                await fetch(
                    `${READ_URL_BASE}${notificationId}/read/`,
                    {
                        method: "POST",

                        headers: {

                            "X-CSRFToken":
                                csrfToken || "",

                            "X-Requested-With":
                                "XMLHttpRequest"
                        },

                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Unable to mark notification as read"
                );
            }


            return await response.json();


        } catch (error) {

            console.error(
                "Mark notification read error:",
                error
            );

            return null;
        }
    }


    /*
    * ----------------------------------------------------
    * MARK ALL NOTIFICATIONS AS READ
    * ----------------------------------------------------
    */
    async function markAllAsRead() {

        try {

            const response = await fetch(
                "/library/notifications/mark-all-read/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken": csrfToken || "",
                        "X-Requested-With": "XMLHttpRequest"
                    },

                    credentials: "same-origin"
                }
            );


            if (!response.ok) {
                throw new Error(
                    "Unable to mark all notifications as read"
                );
            }


            const data = await response.json();


            if (data.success) {

                /*
                * Remove unread styling
                */
                document
                    .querySelectorAll(".notif__item--unread")
                    .forEach(function (item) {

                        item.classList.remove(
                            "notif__item--unread"
                        );

                    });


                /*
                * Remove unread dots
                */
                document
                    .querySelectorAll(".notif__unread-dot")
                    .forEach(function (dot) {

                        dot.remove();

                    });


                /*
                * Update notification badge
                */
                updateBadge(0);


                /*
                * Update currently rendered
                * notification objects
                */
                document
                    .querySelectorAll(".notif__item")
                    .forEach(function (item) {

                        item.classList.remove(
                            "notif__item--unread"
                        );

                    });

            }

        } catch (error) {

            console.error(
                "Mark all notifications read error:",
                error
            );

        }
    }


    /*
    * ----------------------------------------------------
    * MARK ALL READ BUTTON
    * ----------------------------------------------------
    */

    const markAllButton =
        document.getElementById(
            "markAllNotificationsRead"
        );


    if (markAllButton) {

        markAllButton.addEventListener(
            "click",
            async function (event) {

                event.preventDefault();
                event.stopPropagation();

                await markAllAsRead();

            }
        );

    }


    /*
     * ----------------------------------------------------
     * NOTIFICATION CLICK
     * ----------------------------------------------------
     */

    async function handleNotificationClick(
        notification,
        element
    ) {

        /*
         * Only mark unread notifications as read.
         */

        if (!notification.is_read) {

            const result =
                await markAsRead(
                    notification.id
                );


            if (
                result &&
                result.success
            ) {

                notification.is_read =
                    true;


                /*
                 * Remove unread styling
                 */

                element.classList.remove(
                    "notif__item--unread"
                );


                /*
                 * Remove unread dot
                 */

                const unreadDot =
                    element.querySelector(
                        ".notif__unread-dot"
                    );


                if (unreadDot) {
                    unreadDot.remove();
                }


                /*
                 * Update badge
                 */

                updateBadge(
                    result.unread_count
                );
            }
        }


        /*
         * Follow notification link
         */

        if (notification.link) {

            window.location.href =
                notification.link;
        }
    }


    /*
     * ----------------------------------------------------
     * OPEN / CLOSE DROPDOWN
     * ----------------------------------------------------
     */

    toggle.addEventListener(
        "click",
        function (event) {

            /*
             * Don't let clicks inside the dropdown
             * bubble back to the toggle.
             */

            if (
                event.target.closest(
                    "#notifDropdown"
                )
            ) {

                return;
            }


            const isHidden =
                dropdown.hidden;


            dropdown.hidden =
                !isHidden;


            /*
             * Refresh notifications when
             * dropdown is opened.
             */

            if (!dropdown.hidden) {

                loadNotifications();
            }
        }
    );


    /*
     * ----------------------------------------------------
     * CLOSE WHEN CLICKING OUTSIDE
     * ----------------------------------------------------
     */

    document.addEventListener(
        "click",
        function (event) {

            if (
                !toggle.contains(
                    event.target
                )
            ) {

                dropdown.hidden = true;
            }
        }
    );


    /*
     * ----------------------------------------------------
     * INITIAL LOAD
     * ----------------------------------------------------
     */

    loadNotifications();


    /*
     * ----------------------------------------------------
     * PERIODIC CHECK
     *
     * Every 30 seconds check for new notifications.
     * If a new unread notification appears,
     * notification.mp3 will play.
     * ----------------------------------------------------
     */

    setInterval(
        loadNotifications,
        30000
    );

})();

