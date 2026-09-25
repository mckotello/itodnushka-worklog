const state = {
    authMode: "login",
    modalMode: "create",
    token: localStorage.getItem("worklog_token"),
    projects: [],
    currentProject: null,
    currentTasks: [],
    activeTimer: null,
    timerInterval: null,
};

const $ = (id) => document.getElementById(id);

function show(id) {
    $(id).classList.remove("hidden");
}

function hide(id) {
    $(id).classList.add("hidden");
}

function formatMoney(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    return `${Number(value).toLocaleString("ru-RU", {
        maximumFractionDigits: 2,
    })} ₽`;
}

function formatHours(value) {
    return `${Number(value || 0).toLocaleString("ru-RU", {
        maximumFractionDigits: 2,
    })} ч`;
}

function formatDuration(seconds) {
    seconds = Math.max(0, Number(seconds || 0));

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return [
        String(hours).padStart(2, "0"),
        String(minutes).padStart(2, "0"),
        String(secs).padStart(2, "0"),
    ].join(":");
}

function formatDate(value) {
    if (!value) {
        return "—";
    }

    return new Date(value).toLocaleDateString("ru-RU");
}

function statusLabel(status) {
    const labels = {
        active: "Активный",
        completed: "Завершён",
        archived: "Архив",
        todo: "К выполнению",
        in_progress: "В работе",
        done: "Готово",
    };

    return labels[status] || status;
}

function badgeClass(status) {
    if (status === "completed") {
        return "badge completed";
    }

    if (status === "archived") {
        return "badge archived";
    }

    return "badge";
}

async function api(path, options = {}) {
    const headers = {
        ...(options.headers || {}),
    };

    if (state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }

    if (options.body && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(path, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        logout();
        throw new Error("Сессия истекла");
    }

    if (response.status === 204) {
        return null;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        throw new Error(data?.detail || "Ошибка запроса");
    }

    return data;
}

function showAuth() {
    hide("dashboard-screen");
    hide("project-screen");
    show("auth-screen");
}

function showDashboard() {
    hide("auth-screen");
    hide("project-screen");
    show("dashboard-screen");
}

function showProjectScreen() {
    hide("auth-screen");
    hide("dashboard-screen");
    show("project-screen");
}

function logout() {
    state.token = null;
    localStorage.removeItem("worklog_token");

    stopTimerInterval();
    showAuth();
}

async function authenticate() {
    const email = $("auth-email").value.trim();
    const password = $("auth-password").value;

    const endpoint =
        state.authMode === "login"
            ? "/auth/login"
            : "/auth/register";

    hide("auth-error");

    try {
        const data = await api(endpoint, {
            method: "POST",
            body: JSON.stringify({
                email,
                password,
            }),
        });

        state.token = data.access_token;
        localStorage.setItem("worklog_token", state.token);

        showDashboard();
        await loadDashboard();
    } catch (error) {
        $("auth-error").textContent = error.message;
        show("auth-error");
    }
}

async function loadDashboard() {
    hide("dashboard-error");

    try {
        const [dashboard, projects] = await Promise.all([
            api("/projects/dashboard"),
            api("/projects/?page=1&limit=100"),
        ]);

        renderDashboard(dashboard);

        state.projects = projects.items || [];
        renderProjects();
    } catch (error) {
        $("dashboard-error").textContent = error.message;
        show("dashboard-error");
    }
}

function renderDashboard(data) {
    $("stat-projects").textContent = data.total_projects;
    $("stat-active").textContent = data.active_projects;
    $("stat-hours").textContent = formatHours(data.total_hours);
    $("stat-cost").textContent = formatMoney(data.total_cost);
    $("stat-budget").textContent = formatMoney(data.total_budget);

    $("stat-percent").textContent =
        data.budget_used_percent === null
            ? "—"
            : `${Number(data.budget_used_percent).toFixed(1)}%`;
}

function renderProjects() {
    const list = $("projects-list");
    list.innerHTML = "";

    $("project-count").textContent =
        `${state.projects.length} ${pluralProjects(state.projects.length)}`;

    if (!state.projects.length) {
        show("projects-empty");
        return;
    }

    hide("projects-empty");

    for (const project of state.projects) {
        const card = document.createElement("article");
        card.className = "project-card";

        card.innerHTML = `
            <span class="${badgeClass(project.status)}">
                ${statusLabel(project.status)}
            </span>

            <h3>${escapeHtml(project.name)}</h3>

            <div class="project-client">
                ${escapeHtml(project.client_name || "Без клиента")}
            </div>

            <div class="project-meta">
                <span>
                    ${project.hourly_rate
                        ? `${formatMoney(project.hourly_rate)}/ч`
                        : "Ставка не задана"}
                </span>

                <span>
                    ${project.deadline
                        ? formatDate(project.deadline)
                        : "Без дедлайна"}
                </span>
            </div>
        `;

        card.addEventListener("click", () => openProject(project.id));

        list.appendChild(card);
    }
}

function pluralProjects(count) {
    const n = count % 100;

    if (n >= 11 && n <= 14) {
        return "проектов";
    }

    switch (n % 10) {
        case 1:
            return "проект";
        case 2:
        case 3:
        case 4:
            return "проекта";
        default:
            return "проектов";
    }
}

async function createProject(event) {
    event.preventDefault();

    hide("project-form-error");

    const payload = {
        name: $("project-name").value.trim(),
        client_name: $("project-client-input").value.trim() || null,
        budget: $("project-budget-input").value
            ? Number($("project-budget-input").value)
            : null,
        hourly_rate: $("project-rate-input").value
            ? Number($("project-rate-input").value)
            : null,
        deadline: $("project-deadline-input").value || null,
        status: $("project-status-input").value,
    };

    try {
        if (state.modalMode === "edit") {
            await api(
                `/projects/${state.currentProject.id}`,
                {
                    method: "PUT",
                    body: JSON.stringify(payload),
                }
            );

            closeProjectModal();

            await openProject(state.currentProject.id);
            return;
        }

        await api("/projects/", {
            method: "POST",
            body: JSON.stringify(payload),
        });

        closeProjectModal();
        $("project-form").reset();

        await loadDashboard();
    } catch (error) {
        $("project-form-error").textContent = error.message;
        show("project-form-error");
    }
}

async function openProject(projectId) {
    try {
        const project = await api(`/projects/${projectId}`);
        state.currentProject = project;

        showProjectScreen();
        renderProject(project);

        await Promise.all([
            loadProjectSummary(projectId),
            loadTasks(projectId),
            loadEntries(projectId),
        ]);

        await loadActiveTimer(projectId);
    } catch (error) {
        alert(error.message);
    }
}

function renderProject(project) {
    $("project-title").textContent = project.name;
    $("project-client").textContent =
        project.client_name || "Без клиента";

    $("project-status").textContent = statusLabel(project.status);
    $("project-status").className = badgeClass(project.status);
}

async function loadProjectSummary(projectId) {
    const summary = await api(`/projects/${projectId}/summary`);

    $("project-hours").textContent = formatHours(summary.total_hours);
    $("project-cost").textContent = formatMoney(summary.total_cost);
    $("project-budget").textContent = formatMoney(summary.budget);
    $("project-remaining").textContent =
        formatMoney(summary.remaining_budget);
}

async function loadTasks(projectId) {
    const data = await api(
        `/projects/${projectId}/tasks/?page=1&limit=100`
    );

    state.currentTasks = data.items || [];

    const select = $("timer-task");
    select.innerHTML = `<option value="">Без задачи</option>`;

    for (const task of state.currentTasks) {
        const option = document.createElement("option");
        option.value = task.id;
        option.textContent = task.name;
        select.appendChild(option);
    }

    renderTasks();
}

function renderTasks() {
    const list = $("tasks-list");
    list.innerHTML = "";

    if (!state.currentTasks.length) {
        list.innerHTML = `
            <div class="muted">
                Задач пока нет.
            </div>
        `;
        return;
    }

    for (const task of state.currentTasks) {
        const item = document.createElement("div");
        item.className = "list-item";

        item.innerHTML = `
            <div class="list-main">
                <strong>${escapeHtml(task.name)}</strong>
                <span>${statusLabel(task.status)}</span>
            </div>

            <div class="list-actions">
                <button class="small-button"
                        data-task-id="${task.id}"
                        data-action="toggle-task">
                    ${task.status === "done"
                        ? "Вернуть"
                        : "Готово"}
                </button>

                <button class="small-button"
                        data-task-id="${task.id}"
                        data-action="delete-task">
                    Удалить
                </button>
            </div>
        `;

        list.appendChild(item);
    }

    list.querySelectorAll("[data-action='toggle-task']")
        .forEach(button => {
            button.addEventListener("click", () =>
                toggleTask(Number(button.dataset.taskId))
            );
        });

    list.querySelectorAll("[data-action='delete-task']")
        .forEach(button => {
            button.addEventListener("click", () =>
                deleteTask(Number(button.dataset.taskId))
            );
        });
}

async function createTask(event) {
    event.preventDefault();

    const name = $("task-name").value.trim();

    if (!name || !state.currentProject) {
        return;
    }

    try {
        await api(
            `/projects/${state.currentProject.id}/tasks/`,
            {
                method: "POST",
                body: JSON.stringify({
                    name,
                }),
            }
        );

        $("task-form").reset();

        await loadTasks(state.currentProject.id);
    } catch (error) {
        alert(error.message);
    }
}

async function toggleTask(taskId) {
    const task = state.currentTasks.find(
        item => item.id === taskId
    );

    if (!task) {
        return;
    }

    const newStatus =
        task.status === "done"
            ? "todo"
            : "done";

    try {
        await api(
            `/projects/${state.currentProject.id}/tasks/${taskId}`,
            {
                method: "PUT",
                body: JSON.stringify({
                    status: newStatus,
                }),
            }
        );

        await loadTasks(state.currentProject.id);
    } catch (error) {
        alert(error.message);
    }
}

async function deleteTask(taskId) {
    if (!confirm("Удалить задачу?")) {
        return;
    }

    try {
        await api(
            `/projects/${state.currentProject.id}/tasks/${taskId}`,
            {
                method: "DELETE",
            }
        );

        await loadTasks(state.currentProject.id);
    } catch (error) {
        alert(error.message);
    }
}

async function loadEntries(projectId) {
    const data = await api(
        `/projects/${projectId}/time-entries/?page=1&limit=100`
    );

    const list = $("entries-list");
    list.innerHTML = "";

    if (!data.items.length) {
        list.innerHTML = `
            <div class="muted">
                Записей времени пока нет.
            </div>
        `;
        return;
    }

    for (const entry of data.items) {
        const task = state.currentTasks.find(
            item => item.id === entry.task_id
        );

        const item = document.createElement("div");
        item.className = "list-item";

        item.innerHTML = `
            <div class="list-main">
                <strong>
                    ${escapeHtml(task?.name || "Без задачи")}
                </strong>

                <span>
                    ${formatDateTime(entry.started_at)}
                    →
                    ${entry.ended_at
                        ? formatDateTime(entry.ended_at)
                        : "идёт сейчас"}
                </span>
            </div>

            <div class="list-actions">
                <strong>
                    ${formatDuration(entry.duration_seconds)}
                </strong>

                <button
                    class="small-button"
                    data-entry-id="${entry.id}"
                    data-action="delete-entry"
                >
                    Удалить
                </button>
            </div>
        `;

        list.appendChild(item);
    }

    list.querySelectorAll("[data-action='delete-entry']")
        .forEach(button => {
            button.addEventListener("click", () =>
                deleteTimeEntry(Number(button.dataset.entryId))
            );
        });
}
async function deleteTimeEntry(entryId) {
    if (!state.currentProject) {
        return;
    }

    const confirmed = confirm(
        "Удалить эту запись времени?"
    );

    if (!confirmed) {
        return;
    }

    try {
        await api(
            `/projects/${state.currentProject.id}/time-entries/${entryId}`,
            {
                method: "DELETE",
            }
        );

        await loadProjectSummary(state.currentProject.id);
        await loadEntries(state.currentProject.id);
        await loadActiveTimer(state.currentProject.id);
    } catch (error) {
        alert(error.message);
    }
}
function formatDateTime(value) {
    if (!value) {
        return "—";
    }

    return new Date(value).toLocaleString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

async function loadActiveTimer(projectId) {
    const entries = await api(
        `/projects/${projectId}/time-entries/?page=1&limit=100`
    );

    state.activeTimer =
        entries.items.find(entry => !entry.ended_at) || null;

    renderTimer();
}

function renderTimer() {
    stopTimerInterval();

    if (!state.activeTimer) {
        $("timer-status").textContent = "Не запущен";
        $("timer-status").className = "timer-status";
        $("timer-value").textContent = "00:00:00";
        $("timer-btn").textContent = "Запустить таймер";
        return;
    }

    $("timer-status").textContent = "Таймер запущен";
    $("timer-status").className = "timer-status running";
    $("timer-btn").textContent = "Остановить таймер";

    const update = () => {
        const started = new Date(
            state.activeTimer.started_at
        ).getTime();

        const elapsed =
            Math.floor((Date.now() - started) / 1000);

        $("timer-value").textContent =
            formatDuration(elapsed);
    };

    update();
    state.timerInterval = setInterval(update, 1000);
}

function stopTimerInterval() {
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }
}

async function toggleTimer() {
    if (!state.currentProject) {
        return;
    }

    try {
        if (state.activeTimer) {
            await api(
                `/projects/${state.currentProject.id}/time-entries/stop`,
                {
                    method: "POST",
                }
            );
        } else {
            const taskId = $("timer-task").value;

            const data = await api(
                `/projects/${state.currentProject.id}/time-entries/start`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        task_id: taskId
                            ? Number(taskId)
                            : null,
                    }),
                }
            );

            state.activeTimer = data;
        }

        await loadProjectSummary(state.currentProject.id);
        await loadEntries(state.currentProject.id);
        await loadActiveTimer(state.currentProject.id);
    } catch (error) {
        alert(error.message);
    }
}

async function deleteProject() {
    if (!state.currentProject) {
        return;
    }

    const confirmed = confirm(
        `Удалить проект «${state.currentProject.name}»?`
    );

    if (!confirmed) {
        return;
    }

    try {
        await api(
            `/projects/${state.currentProject.id}`,
            {
                method: "DELETE",
            }
        );

        state.currentProject = null;
        showDashboard();
        await loadDashboard();
    } catch (error) {
        alert(error.message);
    }
}

function openProjectModal() {
    state.modalMode = "create";

    $("modal-title").textContent = "Новый проект";
    $("project-submit").textContent = "Создать проект";

    $("project-form").reset();
    hide("project-form-error");

    show("modal");
}

function openEditProjectModal() {
    if (!state.currentProject) {
        return;
    }

    const project = state.currentProject;

    state.modalMode = "edit";

    $("modal-title").textContent = "Редактировать проект";
    $("project-submit").textContent = "Сохранить";

    $("project-name").value = project.name || "";
    $("project-client-input").value = project.client_name || "";
    $("project-budget-input").value =
        project.budget !== null && project.budget !== undefined
            ? project.budget
            : "";
    $("project-rate-input").value =
        project.hourly_rate !== null && project.hourly_rate !== undefined
            ? project.hourly_rate
            : "";
    $("project-deadline-input").value =
        project.deadline || "";
    $("project-status-input").value =
        project.status || "active";

    hide("project-form-error");

    show("modal");
}

function closeProjectModal() {
    hide("modal");
    hide("project-form-error");
}
function closeProjectModal() {
    hide("modal");
    hide("project-form-error");
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".tab")
            .forEach(item => item.classList.remove("active"));

        tab.classList.add("active");

        state.authMode = tab.dataset.auth;

        $("auth-submit").textContent =
            state.authMode === "login"
                ? "Войти"
                : "Зарегистрироваться";

        hide("auth-error");
    });
});

$("auth-form").addEventListener("submit", event => {
    event.preventDefault();
    authenticate();
});

$("logout-btn").addEventListener("click", logout);
$("logout-btn-project").addEventListener("click", logout);

$("refresh-btn").addEventListener(
    "click",
    loadDashboard
);

$("new-project-btn").addEventListener(
    "click",
    openProjectModal
);

$("empty-new-project").addEventListener(
    "click",
    openProjectModal
);

$("close-modal").addEventListener(
    "click",
    closeProjectModal
);

$("modal").addEventListener("click", event => {
    if (event.target === $("modal")) {
        closeProjectModal();
    }
});

$("project-form").addEventListener(
    "submit",
    createProject
);

$("back-btn").addEventListener("click", async () => {
    state.currentProject = null;
    stopTimerInterval();

    showDashboard();
    await loadDashboard();
});

$("task-form").addEventListener(
    "submit",
    createTask
);

$("timer-btn").addEventListener(
    "click",
    toggleTimer
);

$("delete-project-btn").addEventListener(
    "click",
    deleteProject
);
$("edit-project-btn").addEventListener(
    "click",
    openEditProjectModal
);
if (state.token) {
    showDashboard();
    loadDashboard().catch(() => {
        logout();
    });
} else {
    showAuth();
}