from flask import redirect, request
from app.constants import (
    AF_TASKS_KEYS,
    TASK_DETAILS_JS_HELPERS
)
import app.user
from app.userUi import htmlBase, showPleaseLogin
from app.userUi import mycursor, mydb  # reuse db cursor from userUi



def createEntrypoints(webapp):

    @webapp.get("/ui/<sessionUUID>/tasks")
    def entrypoint_ui_list_tasks(sessionUUID):
        logged_in_user = app.user.isLoggedIn(sessionUUID)
        if not logged_in_user:
            return showPleaseLogin()

        is_admin = bool(logged_in_user.get("is_admin") == 1)
        create_url = f"/ui/{sessionUUID}/tasks/create"
        selected_user = request.args.get("userId", "all")

        thead_cols = [
            "          <th>ID</th>",
            "          <th>Name</th>",
        ]
        if is_admin:
            thead_cols.append("          <th>Owner</th>")

        thead_cols.extend([
            "          <th>Enabled</th>",
            "          <th>Model preset</th>",
            "          <th></th>",  # details
            "          <th></th>",  # edit
            "          <th></th>",  # log
            "          <th></th>",  # download
            "          <th></th>",  # delete
        ])

        filter_html = '<div id="admin-filter"></div>' if is_admin else ""

        html = f"""
        <div class="content-card">
        <div class="tasks-header">
            <h1 class="tasks-title">Tasks</h1>
            <div style="display:flex; gap:1rem; align-items:center;">
            {filter_html}
            <a href="{create_url}" class="btn">Create new task</a>
            </div>
        </div>

        <div id="empty-state" style="display:none;">
            <p>No tasks found.</p>
        </div>

        <div class="tasks-table-wrapper" id="table-wrapper" style="display:none;">
            <table class="tasks-table">
            <thead>
                <tr>
                {"".join(thead_cols)}
                </tr>
            </thead>
            <tbody id="tasks-body"></tbody>
            </table>
        </div>
        </div>

        <script>
        const sessionUUID = "{sessionUUID}";
        const isAdmin = {str(is_admin).lower()};
        const selectedUserFromServer = "{selected_user}";

        const ICONS = {{
            details: `
            <svg class="svg-icon svg-icon--details" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M360.08448 352.17408h276.48v40.96h-276.48zM360.08448 458.61376h276.48v40.96h-276.48zM360.08448 567.00416h122.88v40.96h-122.88z" />
                <path d="M472.90368 747.52H293.52448V276.48h409.6v223.09376a20.48 20.48 0 0 0 40.96 0V276.48c0-22.58432-18.37568-40.96-40.96-40.96h-409.6c-22.58432 0-40.96 18.37568-40.96 40.96v471.04c0 22.58432 18.37568 40.96 40.96 40.96h179.3792a20.48 20.48 0 0 0 0-40.96z" />
                <path d="M765.57312 745.984l-54.7328-55.76192a106.73664 106.73664 0 0 0 16.78336-57.43616c0-59.28448-48.2304-107.52-107.52-107.52s-107.52 48.23552-107.52 107.52 48.2304 107.52 107.52 107.52c23.36256 0 44.94336-7.57248 62.59712-20.2752l53.632 54.64576a20.4288 20.4288 0 0 0 14.6176 6.13376 20.48 20.48 0 0 0 14.62272-34.82624z m-145.46944-46.63808c-36.70016 0-66.56-29.85984-66.56-66.56s29.85984-66.56 66.56-66.56 66.56 29.85984 66.56 66.56-29.85472 66.56-66.56 66.56z" />
            </svg>
            `,
            edit: `
            <svg class="svg-icon svg-icon--edit" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M834.3 705.7c0 82.2-66.8 149-149 149H325.9c-82.2 0-149-66.8-149-149V346.4c0-82.2 66.8-149 149-149h129.8v-42.7H325.9c-105.7 0-191.7 86-191.7 191.7v359.3c0 105.7 86 191.7 191.7 191.7h359.3c105.7 0 191.7-86 191.7-191.7V575.9h-42.7v129.8z" />
                <path d="M889.7 163.4c-22.9-22.9-53-34.4-83.1-34.4s-60.1 11.5-83.1 34.4L312 574.9c-16.9 16.9-27.9 38.8-31.2 62.5l-19 132.8c-1.6 11.4 7.3 21.3 18.4 21.3 0.9 0 1.8-0.1 2.7-0.2l132.8-19c23.7-3.4 45.6-14.3 62.5-31.2l411.5-411.5c45.9-45.9 45.9-120.3 0-166.2zM362 585.3L710.3 237 816 342.8 467.8 691.1 362 585.3zM409.7 730l-101.1 14.4L323 643.3c1.4-9.5 4.8-18.7 9.9-26.7L436.3 720c-8 5.2-17.1 8.7-26.6 10z m449.8-430.7l-13.3 13.3-105.7-105.8 13.3-13.3c14.1-14.1 32.9-21.9 52.9-21.9s38.8 7.8 52.9 21.9c29.1 29.2 29.1 76.7-0.1 105.8z" />
            </svg>
            `,
            eye: `
            <svg class="svg-icon svg-icon--eye" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 5c-6.5 0-10 7-10 7s3.5 7 10 7 10-7 10-7-3.5-7-10-7zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10z"/>
                <path d="M12 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/>
            </svg>
            `,
            download: `
            <svg class="svg-icon svg-icon--download" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M505.6 704c5.12 5.12 11.52 7.68 18.56 7.68s13.44-2.56 18.56-7.68l211.2-211.2c10.24-10.24 10.24-26.88 0-37.12s-26.88-10.24-37.12 0L544 626.56V128c0-14.08-11.52-25.6-25.6-25.6s-25.6 11.52-25.6 25.6v498.56L307.36 455.68c-10.24-10.24-26.88-10.24-37.12 0s-10.24 26.88 0 37.12L505.6 704z"/>
                <path d="M128 768c0-14.08-11.52-25.6-25.6-25.6S76.8 753.92 76.8 768v76.8c0 42.24 34.56 76.8 76.8 76.8h716.8c42.24 0 76.8-34.56 76.8-76.8V768c0-14.08-11.52-25.6-25.6-25.6s-25.6 11.52-25.6 25.6v76.8c0 14.08-11.52 25.6-25.6 25.6H153.6c-14.08 0-25.6-11.52-25.6-25.6V768z"/>
            </svg>
            `,
            trash: `
            <svg class="svg-icon svg-icon--delete" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M984.92286 94.607812 664.171936 94.607812 664.171936 79.943717c0-43.271861-35.23101-78.479631-78.502871-78.479631l-142.736718 0c-43.271861 0-78.479631 35.207771-78.479631 78.479631l0 14.664095L43.72503 94.607812c-12.828178 0-23.239453 10.411275-23.239453 23.239453s10.411275 23.239453 23.239453 23.239453l59.748633 0 75.99301 861.718902c1.045775 12.014797 11.108458 21.194381 23.146495 21.194381l618.796904 0c12.061276 0 22.07748-9.202823 23.146495-21.194381l75.969771-861.718902 64.396523 0c12.851417 0 23.239453-10.411275 23.239453-23.239453S997.751038 94.607812 984.92286 94.607812zM410.931621 79.943717c0-17.661984 14.361982-32.000726 32.000726-32.000726l142.736718 0c17.661984 0 32.023966 14.361982 32.023966 32.000726l0 14.664095-206.76141 0L410.931621 79.943717zM800.099494 977.521095 223.877267 977.521095 150.138484 141.086717 873.838277 141.086717 800.099494 977.521095z" />
                <path d="M363.267503 820.65479c12.828178 0 23.239453-10.388035 23.239453-23.239453L386.506956 355.610104c0-12.828178-10.411275-23.239453-23.239453-23.239453s-23.239453 10.411275-23.239453 23.239453l0 441.805233C340.028051 810.243515 350.439326 820.65479 363.267503 820.65479z" />
                <path d="M514.323945 820.65479c12.851417 0 23.239453-10.388035 23.239453-23.239453L537.563398 355.610104c0-12.828178-10.388035-23.239453-23.239453-23.239453-12.828178 0-23.239453 10.411275-23.239453 23.239453l0 441.805233C491.084493 810.243515 501.495767 820.65479 514.323945 820.65479z" />
                <path d="M665.380387 820.65479c12.851417 0 23.239453-10.388035 23.239453-23.239453L688.61984 355.610104c0-12.828178-10.388035-23.239453-23.239453-23.239453s-23.239453 10.411275-23.239453 23.239453l0 441.805233C642.140935 810.243515 652.52897 820.65479 665.380387 820.65479z" />
            </svg>
            `,
        }};

        function escapeHtml(s) {{
            if (s === null || s === undefined) return "";
            return String(s)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
        }}

        async function apiJson(url, opts) {{
            const res = await fetch(url, opts);
            const text = await res.text();
            try {{
            return JSON.parse(text);
            }} catch {{
            return {{ status: "error", raw: text, httpStatus: res.status }};
            }}
        }}

        function buildOwnerCell(t) {{
            const uid = t.userId ?? t.userid ?? t.user_id;
            const uname = t.user_name ?? t.userName ?? t.owner_name;
            if (uname && uid) return `${{escapeHtml(uname)}} (id=${{escapeHtml(uid)}})`;
            if (uid) return `id=${{escapeHtml(uid)}}`;
            return "-";
        }}

        function renderRow(t) {{
            const taskId = t.id;
            const enabled = Number(t.enabled || 0) === 1;
            const modelPreset = t.model_preset || "-";

            const detailsUrl = `/ui/${{sessionUUID}}/tasks/${{taskId}}`;
            const editUrl = `/ui/${{sessionUUID}}/tasks/${{taskId}}/edit`;
            const downloadUrl = `/api/1.0/${{sessionUUID}}/task/${{taskId}}/result`;

            return `
            <tr>
                <td>${{escapeHtml(taskId)}}</td>
                <td>${{escapeHtml(t.name || "")}}</td>
                ${{isAdmin ? `<td>${{buildOwnerCell(t)}}</td>` : ""}}
                <td class='tasks-enabled-cell'>
                <label class="switch">
                    <input type="checkbox" data-task-id="${{escapeHtml(taskId)}}" ${{enabled ? "checked" : ""}}
                    onchange="toggleTaskEnabled(this, '${{sessionUUID}}')">
                    <span class="slider"></span>
                </label>
                </td>
                <td>${{escapeHtml(modelPreset)}}</td>

                <td>
                <a href='${{detailsUrl}}' class='icon-btn tooltip' data-tooltip="Show details">
                    ${{ICONS.details}}
                </a>
                </td>

                <td>
                <a href='${{editUrl}}' class='icon-btn tooltip' data-tooltip="Edit">
                    ${{ICONS.edit}}
                </a>
                </td>

                <td>
                <button class="icon-btn tooltip" data-tooltip="Show log"
                    onclick="showLog('/api/1.0/${{sessionUUID}}/task/${{taskId}}/log', ${{taskId}})">
                    ${{ICONS.eye}}
                </button>
                </td>

                <td>
                <button class="icon-btn tooltip" data-tooltip="Download result"
                    onclick="downloadResult('${{downloadUrl}}', ${{taskId}})">
                    ${{ICONS.download}}
                </button>
                </td>

                <td>
                <button class="icon-btn tooltip" data-tooltip="Delete"
                    onclick="deleteTask('${{taskId}}', '${{sessionUUID}}')">
                    ${{ICONS.trash}}
                </button>
                </td>
            </tr>
            `;
        }}

        function showEmpty(isEmpty) {{
            document.getElementById("empty-state").style.display = isEmpty ? "block" : "none";
            document.getElementById("table-wrapper").style.display = isEmpty ? "none" : "block";
        }}

        async function renderAdminFilter() {{
            if (!isAdmin) return;
            const container = document.getElementById("admin-filter");
            if (!container) return;

            const usersRes = await apiJson(`/api/1.0/${{sessionUUID}}/user`);
            const users = (usersRes && usersRes.status === "ok" && Array.isArray(usersRes.users)) ? usersRes.users : [];

            const url = new URL(window.location.href);
            const selected = url.searchParams.get("userId") || selectedUserFromServer || "all";

            const options = [
            `<option value="all">All users</option>`,
            ...users.map(u => {{
                const uid = String(u.id);
                const uname = u.name || "";
                const sel = (uid === String(selected)) ? "selected" : "";
                return `<option value="${{escapeHtml(uid)}}" ${{sel}}>${{escapeHtml(uname)}} (id=${{escapeHtml(uid)}})</option>`;
            }})
            ].join("");

            container.innerHTML = `
            <form method="GET">
                <select name="userId" class="task-input userselect" onchange="this.form.submit()">
                ${{options}}
                </select>
            </form>
            `;
        }}

        async function loadTasks() {{
            let apiUrl = `/api/1.0/${{sessionUUID}}/task`;
            if (isAdmin) {{
            const url = new URL(window.location.href);
            const userId = url.searchParams.get("userId");
            if (userId && userId !== "all") {{
                apiUrl += `?userId=${{encodeURIComponent(userId)}}`;
            }}
            }}

            const data = await apiJson(apiUrl);
            const tasks = (data && data.status === "ok" && Array.isArray(data.tasks)) ? data.tasks : [];

            if (!tasks.length) {{
            showEmpty(true);
            return;
            }}

            showEmpty(false);
            document.getElementById("tasks-body").innerHTML = tasks.map(renderRow).join("");
        }}

        (async function init() {{
            await renderAdminFilter();
            await loadTasks();
        }})();
        </script>
        """


        return htmlBase(html, title="Tasks", sessionUUID=sessionUUID, include_styles=True)
    
    @webapp.get("/ui/<sessionUUID>/tasks/create")
    def entrypoint_ui_create_task(sessionUUID):

        logged_in_user = app.user.isLoggedIn(sessionUUID)
        if not logged_in_user:
            return showPleaseLogin()
        user_id = logged_in_user["id"]


        html = f"""
        <div class="content-card" id="createpage" data-userid="{user_id}">
          <h1 style="margin-bottom: 1.5rem; color: #00d4ff; font-size: 2rem; font-weight: 700;">
            Create new task
          </h1>

        <!-- To send the data -->
          <form id="createTaskForm">
            <!-- Name -->
            <div class="task-pr">
              <label class="task-label">Task Name *</label>
              <input type="text" class="task-input" id="task-name" name="name" required>
            </div>

            <!-- User Comment -->
            <div class="task-pr">
              <label class="task-label">User Comment</label>
              <textarea class="task-input" id="task-comment" name="userComment" rows="2"></textarea>
            </div>

            <!-- FASTA -->
            <div class="task-pr">
              <label class="task-label">FASTA Input *</label>
              <textarea class="task-input" id="task-fasta" name="fasta" rows="5" required></textarea>
            </div>

            <!-- Model Preset -->
            <div class="task-pr">
              <label class="task-label">Model Preset</label>
              <select class="task-input" id="task-model_preset" name="modelPreset">
                <option value=""></option>
                <option value="monomer">Monomer</option>
                <option value="monomer_casp14">Monomer CASP14</option>
                <option value="monomer_ptm">Monomer PTM</option>
                <option value="multimer">Multimer</option>
              </select>
            </div>

            <!-- full_dbs -->
            <div class="task-pr">
              <label class="task-label">Database Preset</label>
              <select class="task-input" id="task-full_dbs" name="fullDBS">
                <option value="1">Full DBs (default)</option>
                <option value="0">Reduced DBs</option>
              </select>
            </div>

            <!-- models_to_relax -->
            <div class="task-pr">
              <label class="task-label">Models to Relax</label>
              <select class="task-input" id="task-models_to_relax" name="modelsToRelax">
                <option value="2">Best (default)</option>
                <option value="0">None</option>
                <option value="1">All</option>
              </select>
            </div>

            <!-- enable_gpu_relax -->
            <div class="task-pr">
              <label class="task-label">GPU Relax Enabled</label>
              <div class="task-toggle">
                <label class="switch">
                  <input type="checkbox" id="task-enable_gpu_relax" name="enable_gpu_relax" value="1" checked>
                  <span class="slider"></span>
                </label>
              </div>
            </div>

            <!-- max_template_data -->
            <div class="task-pr">
              <label class="task-label">Max Template Date</label>
              <input type="text" class="task-input" id="task-max_template_data" name="maxTemplateDate" placeholder="YYYY-MM-DD">
            </div>

            <button type="submit" class="task-submit" id="submitcreation">Submit</button>
          </form>
        </div>
        """
        return htmlBase(
            html,
            title="Create Task",
            sessionUUID=sessionUUID,
            include_styles=True,
        )

    @webapp.get("/ui/<sessionUUID>/tasks/<int:taskId>")
    def entrypoint_ui_task_details(sessionUUID, taskId):
        logged_in_user = app.user.isLoggedIn(sessionUUID)
        if not logged_in_user:
            return showPleaseLogin()

        back_url = f"/ui/{sessionUUID}/tasks"
        edit_url = f"/ui/{sessionUUID}/tasks/{taskId}/edit"

        html = f"""
        <div class="content-card">
        <div class="tasks-header">
            <div>
            <h1 class="tasks-title">
                Task details -
                <span class="task-details-id"> ID {taskId}</span>
            </h1>
            </div>

            <div class="tasks-actions">
            <a class="btn btn-small" href="{back_url}">Back</a>
            <a class="btn btn-small" href="{edit_url}">Edit</a>
            </div>
        </div>

        <div id="task-not-found" style="display:none;">
            <h1 style="margin-bottom: 1.5rem; color: #00d4ff; font-size: 2rem; font-weight: 700;">
            Task not found
            </h1>
            <p>The requested task does not exist or you do not have access to it.</p>
        </div>

        <div class="details-grid" id="task-details" style="display:none;"></div>
        </div>

        {TASK_DETAILS_JS_HELPERS}

        <script>
        const sessionUUID = "{sessionUUID}";
        const taskId = {taskId};

        function renderTaskDetails(t) {{
            const owner = (t.user_name && t.userId)
            ? `${{safe(t.user_name)}} (id=${{safe(t.userId)}})`
            : safe(t.user_name);

            const html = `
            <div class="task-pr">
                <span class="task-label">Task Owner</span>
                <span class="task-value">${{owner}}</span>
            </div>

            <div class="task-pr">
                <span class="task-label">Task Name</span>
                <span class="task-value">${{safe(t.name)}}</span>
            </div>

            <div class="task-pr">
                <span class="task-label">Task Enabled</span>
                <span class="task-value">${{yn(t.enabled)}}</span>
            </div>

            <div class="task-pr">
                <span class="task-label">Model preset</span>
                <span class="task-value">${{safe(t.model_preset || "")}}</span>
            </div>

            <div class="task-pr">
                <span class="task-label">Database preset</span>
                <span class="task-value">${{Number(t.full_dbs) === 1 ? "Full DBs" : "Reduced DBs"}}</span>
            </div>

            <div class="task-pr">
                <span class="task-label">Models to relax</span>
                <span class="task-value">
                ${{String(t.models_to_relax) === "2"
                    ? "Best"
                    : (String(t.models_to_relax) === "1" ? "All" : "None")}}
                </span>
            </div>

            <div class="task-pr">
                <span class="task-label">GPU Relax Enabled</span>
                <span class="task-value">${{yn(t.enable_gpu_relax)}}</span>
            </div>

            <div class="task-pr">
                <span class="task-label">Max template date</span>
                <span class="task-value">${{safe(toDateOnly(t.max_template_date))}}</span>
            </div>

            <div class="task-pr full-width">
                <span class="task-label">User comment</span>
                <pre class="task-value task-value-pre">${{safe(t.userComment)}}</pre>
            </div>

            <div class="task-pr full-width">
                <span class="task-label">FASTA</span>
                <pre class="task-value task-value-pre">${{safe(t.fasta)}}</pre>
            </div>
            `;
            return html;
        }}

        async function loadTaskDetails() {{
            const res = await fetch(`/api/1.0/${{sessionUUID}}/task/${{taskId}}`);
            const data = await res.json();

            if (!data || data.status !== "ok" || !data.task) {{
            document.getElementById("task-not-found").style.display = "block";
            return;
            }}

            const container = document.getElementById("task-details");
            container.innerHTML = renderTaskDetails(data.task);
            container.style.display = "grid";
        }}

        loadTaskDetails();
        </script>
        """

        return htmlBase(
            html,
            title="Task details",
            sessionUUID=sessionUUID,
            include_styles=True,
        )

    @webapp.get("/ui/<sessionUUID>/tasks/<int:taskId>/edit")
    def entrypoint_ui_task_edit(sessionUUID, taskId):

        logged_in_user = app.user.isLoggedIn(sessionUUID)
        if not logged_in_user:
            return showPleaseLogin()

        html = f"""
        <div class="content-card"
            id="editpage"
            data-userid="{logged_in_user['id']}"
            data-taskid="{taskId}"
            data-is-admin="{str(bool(logged_in_user.get('is_admin') == 1)).lower()}">

        <h1 style="margin-bottom: 1.5rem; color: #00d4ff; font-size: 2rem; font-weight: 700;">
            Edit Task
        </h1>


        <form id="editTaskForm">

            <div class="task-pr">
            <label class="task-label">Task Name *</label>
            <input type="text" class="task-input" id="task-name" required>
            </div>

            <div class="task-pr" id="admin-owner-wrapper" style="display:none;">
                <label class="task-label">Task Owner</label>
                <select class="task-input" id="task-owner"></select>
            </div>


            <div class="task-pr">
            <label class="task-label">User Comment</label>
            <textarea class="task-input" id="task-comment" rows="2"></textarea>
            </div>

            <div class="task-pr">
            <label class="task-label">FASTA Input *</label>
            <textarea class="task-input" id="task-fasta" rows="5" required></textarea>
            </div>

            <div class="task-pr">
            <label class="task-label">Model Preset</label>
            <select class="task-input" id="task-model_preset">
                <option value=""></option>
                <option value="monomer">Monomer</option>
                <option value="monomer_casp14">Monomer CASP14</option>
                <option value="monomer_ptm">Monomer PTM</option>
                <option value="multimer">Multimer</option>
            </select>
            </div>

            <div class="task-pr">
            <label class="task-label">Database Preset</label>
            <select class="task-input" id="task-full_dbs">
                <option value="1">Full DBs</option>
                <option value="0">Reduced DBs</option>
            </select>
            </div>

            <div class="task-pr">
            <label class="task-label">Models to Relax</label>
            <select class="task-input" id="task-models_to_relax">
                <option value="2">Best</option>
                <option value="1">All</option>
                <option value="0">None</option>
            </select>
            </div>

            <div class="task-pr">
            <label class="task-label">GPU Relax Enabled</label>
            <div class="task-toggle">
                <label class="switch">
                <input type="checkbox" id="task-enable_gpu_relax">
                <span class="slider"></span>
                </label>
            </div>
            </div>

            <div class="task-pr">
            <label class="task-label">Max Template Date</label>
            <input type="text" class="task-input" id="task-max_template_data">
            </div>

            <button type="submit" class="task-submit">Save Changes</button>
        </form>
        </div>
        """

        return htmlBase(
            html,
            title="Edit Task",
            sessionUUID=sessionUUID,
            include_styles=True,
        )
    @webapp.get("/ui/viewer")
    def entrypoint_static_viewer():
        html = """
        <link rel="stylesheet" href="/static/molstar/molstar.css">

        <div class="content-card" style="max-width: 1100px;">
            <div class="tasks-header" style="margin-bottom: 1.5rem;">
                <h1 class="tasks-title">3D Structure Viewer</h1>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.9rem;">
                    AlphaFold predicted models
                </p>
            </div>

            <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                <span style="color: rgba(255,255,255,0.6);
                             font-size: 0.9rem; align-self: center;">
                    Select model:
                </span>
                <button onclick="loadModel(1)" id="btn-1" class="btn btn-small">Model 1</button>
                <button onclick="loadModel(2)" id="btn-2" class="btn btn-small">Model 2</button>
                <button onclick="loadModel(3)" id="btn-3" class="btn btn-small">Model 3</button>
                <button onclick="loadModel(4)" id="btn-4" class="btn btn-small">Model 4</button>
                <button onclick="loadModel(5)" id="btn-5" class="btn btn-small">Model 5</button>
            </div>

            <div style="display:flex; gap:1rem; margin-bottom:1rem; flex-wrap:wrap;">
                <span style="color:rgba(255,255,255,0.6); font-size:0.85rem;">
                    Confidence (pLDDT):
                </span>
                <span style="font-size:0.8rem; display:flex; align-items:center; gap:4px;">
                    <span style="width:12px;height:12px;background:#0053D6;
                                 border-radius:2px;display:inline-block;"></span>
                    Very high (&gt;90)
                </span>
                <span style="font-size:0.8rem; display:flex; align-items:center; gap:4px;">
                    <span style="width:12px;height:12px;background:#65CBF3;
                                 border-radius:2px;display:inline-block;"></span>
                    High (70-90)
                </span>
                <span style="font-size:0.8rem; display:flex; align-items:center; gap:4px;">
                    <span style="width:12px;height:12px;background:#FFDB13;
                                 border-radius:2px;display:inline-block;"></span>
                    Low (50-70)
                </span>
                <span style="font-size:0.8rem; display:flex; align-items:center; gap:4px;">
                    <span style="width:12px;height:12px;background:#FF7D45;
                                 border-radius:2px;display:inline-block;"></span>
                    Very low (&lt;50)
                </span>
            </div>

            <div id="mol-viewer" style="width:100%; height:500px;
                                         border-radius:12px; overflow:hidden;">
            </div>
        </div>

       <script src="/static/molstar/molstar.js"></script>
        <script>
            let viewer = null;
            let models = [];

            function setActiveButton(n) {
                for (let i = 1; i <= 5; i++) {
                    const btn = document.getElementById(`btn-${i}`);
                    btn.style.background = i === n ? 'rgba(0,212,255,0.25)' : '';
                    btn.style.borderColor = i === n ? '#00d4ff' : '';
                    btn.style.color = i === n ? '#00d4ff' : '';
                }
            }

            async function loadModel(modelNumber) {
                if (!viewer || models.length === 0) return;
                setActiveButton(modelNumber);
                await viewer.clear();
                await viewer.loadStructureFromUrl(models[modelNumber - 1].url, 'pdb');
            }

            async function start() {
                viewer = await molstar.Viewer.create('mol-viewer', {
                    layoutIsExpanded: false,
                    layoutShowControls: false,
                    layoutShowSequence: false,
                    layoutShowLog: false,
                });

                // Fetch model list from API
                const res = await fetch('/api/models');
                models = await res.json();
                console.log('Models loaded:', models);

                // Load first model automatically
                if (models.length > 0) {
                    setActiveButton(1);
                    await viewer.loadStructureFromUrl(models[0].url, 'pdb');
                }
            }

            document.addEventListener('DOMContentLoaded', start);
        </script>
        """
        return htmlBase(html, title="3D Viewer", sessionUUID="", include_styles=True)