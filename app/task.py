#This file acts like a controller
import os # used for create and download results
import sys # used for writing in log file (.txt)
from flask import request, send_from_directory, redirect
import app.user as user
import app.constants as constants
from app.userUi import htmlBase, showPleaseLogin

mycursor = None
mydb = None
# connect to the mysql, get cursor to run quesries
try:
  from app.dbUtil import getDbInstance
  mydb = getDbInstance()
  mycursor = mydb.cursor()
except:
  print("Error occured while connecting to the DB")


# for debuging
def trace(text):
    print(text, file=sys.stderr)

# get a specific task from the database, return as a structured dictionary
def getTask(taskId, logged_in_user):
  # validate taskId
  if taskId is None or not str(taskId).isdigit():
    return None

  taskId_int = int(taskId)
  
  if taskId_int is None or f"{taskId_int}" != f"{taskId}":
    return None

  task = []
  try:
    # if user is admin, he can see any task by the ID
    # for admin we also join with users table to get owner information
    if logged_in_user["is_admin"]:
      mycursor.execute(
        constants.SQL_SELECT_TASKS_WITH_USER + " WHERE t.id = %s",
        [taskId_int]
      )
      task = mycursor.fetchall()

      if task and task[0]:
        # includes user_name and userId from joined query
        return dict(zip(constants.AF_TASKS_KEYS_WITH_USER, task[0]))
      return None

    # if not admin, user can only see his own tasks
    mycursor.execute(
      constants.SQL_SELECT_TASK_BY_ID + " AND userId = %s",
      [taskId_int, logged_in_user["id"]]
    )
    task = mycursor.fetchall()

  except Exception as exc:
    trace(f"Error while fetching task from database for task: {taskId_int}: {exc}")
    return None

  # ensures that the query result is not empty and that the first returned record contains valid data
  if task and task[0]:
    # convert raw database row into a dictionary by mapping column names to values using zip
    task_dict = dict(zip(constants.AF_TASKS_KEYS, task[0]))

    # add owner name explicitly for UI convenience (safe for non-admin)
    task_dict["user_name"] = logged_in_user.get("name")
    return task_dict
  else:
    return None

# The functions are called when the endpoint is accessed
def createEntrypoints(webapp):
  
  @webapp.get("/api/1.0/<sessionUUID>/task")
  def entrypoint_list_tasks(sessionUUID):
      logged_in_user = user.isLoggedIn(sessionUUID)
      if not logged_in_user:
          return constants.PLEASE_LOGIN

      tasks = []
      try:
          is_admin = bool(logged_in_user.get("is_admin") == 1)

          if is_admin:
              selected_user = request.args.get("userId", "all")

              if selected_user != "all":
                  mycursor.execute(
                      constants.SQL_SELECT_TASKS_WITH_USER + " WHERE t.userId = %s",
                      [selected_user],
                  )
              else:
                  mycursor.execute(constants.SQL_SELECT_TASKS_WITH_USER)

              rows = mycursor.fetchall()
              tasks = [dict(zip(constants.AF_TASKS_KEYS_WITH_USER, row)) for row in rows]
          else:
              mycursor.execute(
                  constants.SQL_SELECT_TASKS + " WHERE userId = %s",
                  [logged_in_user["id"]],
              )
              rows = mycursor.fetchall()
              tasks = [dict(zip(constants.AF_TASKS_KEYS, row)) for row in rows]

      except Exception as exc:
          trace(f"Error while fetching tasks from database: {exc}")
          tasks = []

      if tasks and len(tasks) > 0:
          return {"status": "ok", "tasks": tasks}
      else:
          return constants.DNF_RESPONSE
    
  @webapp.put("/api/1.0/<sessionUUID>/task")
  def entrypoint_insert_task(sessionUUID):
    if not user.isLoggedIn(sessionUUID):
      return constants.PLEASE_LOGIN

    userData = {}
    try:
      userData = request.get_json(force=True, cache=True)
    except:
      trace('Unable to process the incoming request. Please check your request body.')
      return {"status": "invalid request" }, 400

    if not userData.get(constants.AF_TASKS_INPUT_KEYS['userId'], ''):
        return {"status": "invalid request. userId is required." }, 400
    
    if userData:  
      values = create_tasks_tuple(userData)
      try:
        mycursor.execute(constants.SQL_INSERT_TASK, values)
        mydb.commit() 

        if mycursor.rowcount > 0:
          trace(f"Saved recoed in database with task id of {mycursor.lastrowid}")
        else:
          trace("No record is saved in database.")
          
      except:
        trace('An error has occured while inserting the task in the database.')
        return {"status": "Unexpected error occured." }, 500
      

    return {"status": "Task saved." }, 201
       
  @webapp.get("/api/1.0/<sessionUUID>/task/<taskId>")
  def entrypoint_show_task(sessionUUID, taskId):
    logged_in_user = user.isLoggedIn(sessionUUID)
    if not logged_in_user:
      return constants.PLEASE_LOGIN

    if taskId is None or str(taskId).strip() == "":
      return { "status": "error", "message": "taskId is required." }, 400

    try:
      task = getTask(taskId, logged_in_user)
      if not task:
        return constants.DNF_RESPONSE

      return { "status": "ok", "task": task }

    except Exception as exc:
      trace(f"Error in entrypoint_show_task: {exc}")
      # trace(traceback.format_exc())
      return { "status": "error", "message": "Could not fetch task." }, 500

  @webapp.delete("/api/1.0/<sessionUUID>/task/<taskId>")
  def entrypoint_remove_task(sessionUUID, taskId):
    logged_in_user = user.isLoggedIn(sessionUUID)
    if not logged_in_user:
      return constants.PLEASE_LOGIN

    deleted_rowcount = -1

    if taskId is None or not str(taskId).isdigit():
      return constants.DNF_RESPONSE
  
    try:
      if logged_in_user["is_admin"]:
        mycursor.execute(constants.SQL_DELETE_TASK, [taskId])
      else:
        mycursor.execute(constants.SQL_DELETE_TASK + " AND userId = %s", [taskId, logged_in_user["id"]])
      deleted_rowcount = mycursor.rowcount
      mydb.commit()
      trace(f"Deleted task for record {taskId}.")
    except:
      trace("Error while deleting task(s) from database")
      deleted_rowcount = 0
      
    if deleted_rowcount > 0:
      return { "status": "ok" }
    else:
      return constants.DNF_RESPONSE

  @webapp.post("/api/1.0/<sessionUUID>/task/<taskId>/enabled")
  def entrypoint_set_task_enabled(sessionUUID, taskId):
    logged_in_user = user.isLoggedIn(sessionUUID)
    if not logged_in_user:
      return constants.PLEASE_LOGIN

    if taskId is None or not str(taskId).isdigit():
      return { "status": "error", "message": "taskId is required." }, 400

    try:
      payload = request.get_json(force=True, cache=True) or {}
    except Exception:
      return { "status": "error", "message": "invalid request" }, 400

    enabled = payload.get("enabled", None)
    if enabled not in (0, 1, "0", "1"):
      return { "status": "error", "message": "invalid enabled value" }, 400

    enabled_int = int(enabled)

    try:
      if logged_in_user["is_admin"]:
        mycursor.execute(
          "UPDATE af_tasks SET enabled = %s WHERE id = %s",
          [enabled_int, int(taskId)]
        )
      else:
        mycursor.execute(
          "UPDATE af_tasks SET enabled = %s WHERE id = %s AND userId = %s",
          [enabled_int, int(taskId), logged_in_user["id"]]
        )

      if mycursor.rowcount == 0:
        return constants.DNF_RESPONSE

      mydb.commit()
      return { "status": "ok" }

    except Exception as exc:
      trace(f"Error while updating enabled for task {taskId}: {exc}")
      return { "status": "error", "message": "Could not update task." }, 500


  @webapp.post("/api/1.0/<sessionUUID>/task/<taskId>")
  def entrypoint_edit_task(sessionUUID, taskId):

      logged_in_user = user.isLoggedIn(sessionUUID)
      if not logged_in_user:
          return constants.PLEASE_LOGIN

      is_admin = bool(logged_in_user.get("is_admin") == 1)

      try:
          userData = request.get_json(force=True, cache=True)
      except:
          trace("Invalid JSON body")
          return {"status": "invalid request"}, 400

      # userId must exist
      if not userData.get(constants.AF_TASKS_INPUT_KEYS["userId"]):
          return {"status": "invalid request. userId is required."}, 400

      # Non-admins are not allowed to change owner
      if not is_admin:
          userData["userId"] = logged_in_user["id"]

      # build update query
      result_type, result = create_update_sql(userData, taskId, logged_in_user)

      if result_type == "ERROR":
          return result

      sql, values = result

      try:
          mycursor.execute(sql, values)
          mydb.commit()

          if mycursor.rowcount > 0:
              trace(f"Updated task {taskId}")
              return {
                  "status": "success",
                  "message": f"Task {taskId} updated."
              }
          else:
              return {
                  "status": "warning",
                  "message": f"No task updated"
              }

      except Exception as e:
          trace(f"DB error while updating task {taskId}: {e}")
          return {"status": "Unexpected error occured."}, 500
  
  @webapp.get("/api/1.0/<sessionUUID>/task/<taskId>/result")
  def entrypoint_return_result(sessionUUID, taskId):
    logged_in_user = user.isLoggedIn(sessionUUID)
    if not logged_in_user:
      return constants.PLEASE_LOGIN

    task = getTask(taskId,logged_in_user)
    if task is not None:
      fName = os.path.join("results",f"{task['userId']}",f"{task['id']}.zip")
      if os.path.exists(fName):
        return send_from_directory(
            directory="..", path=fName, as_attachment=True
        )
      
      return { "status": "Result File Not Found" }, 404
    else:
      return constants.DNF_RESPONSE

  @webapp.get("/api/1.0/<sessionUUID>/task/<taskId>/log")
  def entrypoint_return_log(sessionUUID, taskId):
    logged_in_user = user.isLoggedIn(sessionUUID)
    if not logged_in_user:
      return constants.PLEASE_LOGIN

    task = getTask(taskId, logged_in_user)
    if task is not None:
      fName = os.path.join("results",f"{task['userId']}",f"{task['id']}.log")
      if os.path.exists(fName):
        return send_from_directory(
            directory="..", path=fName, as_attachment=True, mimetype="application/txt"
        )
      
      return { "status": "Log File Not Found" }, 404
    else:
      return constants.DNF_RESPONSE

  @webapp.get("/api/models")
  def entrypoint_get_models():
      models = []
      for i in range(1, 6):
          models.append({
              "name": f"Model {i}",
              "url": f"/static/example/unrelaxed_model_{i}_pred_0.pdb"
          })
      from flask import jsonify
      return jsonify(models)
def create_tasks_tuple(input_data):
    const_input_keys = constants.AF_TASKS_INPUT_KEYS

    enabled_value = input_data.get(const_input_keys['enabled'], 0)
    user_id_value = input_data[const_input_keys['userId']]

    task_name_value = input_data.get(const_input_keys['task_name'],'')
    user_comment_value = input_data.get(const_input_keys['user_comment'],'')
    fasta_data_value = input_data.get(const_input_keys['fasta'],'')
    model_preset_value = input_data.get(const_input_keys['preset'],'')

    full_dbs_value = input_data.get(const_input_keys['dbs'], 1) 
    models_to_relax_value = input_data.get(const_input_keys['models_to_relax'], 2)
    enable_gpu_relax = int(
        input_data.get(constants.AF_TASKS_INPUT_KEYS["gpu_relax"], 0)
    )
    max_template_data_value = input_data.get(const_input_keys['template_date'], '')

    values = (
        enabled_value,
        user_id_value,
        task_name_value,
        user_comment_value,
        fasta_data_value,
        model_preset_value,
        full_dbs_value,
        models_to_relax_value,
        enable_gpu_relax,
        max_template_data_value
    )

    return values

def create_update_sql(userData, taskId, logged_in_user):


  set_clauses = []
  values = []
  
  for json_key, updated_value in userData.items():
    db_column_name = constants.AF_TASKS_INPUT_KEYS_TO_DB.get(json_key)

    if db_column_name and db_column_name in constants.ALLOWED_UPDATE_FIELDS:
      set_clauses.append(f"{db_column_name} = %s")
      values.append(updated_value)
  
  if not set_clauses:
    return ("ERROR", ({"status": "error", "message": "No valid fields provided for update."},400))
  
  sql = f"UPDATE af_tasks SET {', '.join(set_clauses)} " + "WHERE id = %s"
  values.append(taskId)

  if logged_in_user["is_admin"]:
     modified_sql = sql 
  else:
    modified_sql = sql + " AND userId = %s"
    values.append(logged_in_user["id"])
  return ("SQL", (modified_sql, values))
  
