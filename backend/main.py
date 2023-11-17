from fastapi import FastAPI, HTTPException
import numpy as np
import psycopg2
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware
import httpx
import requests


# Load environment variables from .env file
load_dotenv()

# Get environment variables
PGUSER = os.getenv("PGUSER")
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT")
PGDATABASE = os.getenv("PGDATABASE")
PGPASSWORD = os.getenv("PGPASSWORD")

# Global variables to store the pre-loaded data
picks_data = None
tasks_data = None
robots_data = None
sites_data = None
objects_data = None
destinations_data = None


# Instantiate the FastAPI app with picks_data and tasks_data from postgres db
@asynccontextmanager
async def lifespan(app: FastAPI):
    global picks_data, tasks_data, robots_data, sites_data, objects_data, destinations_data

    # Connect to the database
    conn = psycopg2.connect(
        dbname=PGDATABASE, user=PGUSER, password=PGPASSWORD, host=PGHOST, port=PGPORT
    )

    # Create a cursor object
    cur = conn.cursor()

    # Fetch picks data with robot_id
    cur.execute(
        """
SELECT 
    p.start_pick_time AT TIME ZONE 'UTC' as start_pick_time_utc, 
    p.pick_object,
    EXTRACT(EPOCH FROM (p.end_pick_time - p.start_pick_time)) as duration,
    e.robot_id,
    3600 / EXTRACT(EPOCH FROM (p.end_pick_time - p.start_pick_time)) as pph,
    e.description
FROM execution_data_pick p
JOIN execution_data_task t ON p.task_id = t.id
JOIN execution_data_run r ON t.run_id = r.id
JOIN execution_data_experiment e ON r.experiment_id = e.id
WHERE EXTRACT(EPOCH FROM (p.end_pick_time - p.start_pick_time)) > 0
AND extract(EPOCH from (p.end_pick_time - p.start_pick_time)) <= 5
AND extract(EPOCH from (p.end_pick_time - p.start_pick_time)) > 1
AND p.failure_state = 'succeeded';
    """
    )
    picks_data = np.array(cur.fetchall())

    # Fetch tasks data with robot_id
    cur.execute(
        """
   SELECT 
    first_pick.pick_object,
    t.success, 
    EXTRACT(EPOCH FROM (t.end_date - t.start_date)) as duration, 
    EXTRACT(EPOCH FROM sp.successful_picks_duration) AS successful_picks_duration,
    COALESCE(sp.successful_pick_count, 0) AS successful_pick_count,
    COALESCE(up.unsuccessful_pick_count, 0) AS unsuccessful_pick_count,
    t.start_date AT TIME ZONE 'UTC' as start_date_utc, 
    t.id, 
    e.robot_id, 
    e.description
FROM 
    execution_data_task t
JOIN 
    execution_data_run r ON t.run_id = r.id
JOIN 
    execution_data_experiment e ON r.experiment_id = e.id
LEFT JOIN 
    (SELECT 
        task_id, 
        pick_object 
     FROM 
        execution_data_pick 
     WHERE 
        pick_object IS NOT NULL 
     GROUP BY task_id, pick_object 
    ) AS first_pick ON t.id = first_pick.task_id
LEFT JOIN 
    (SELECT 
        task_id, 
        COUNT(*) AS successful_pick_count,
        SUM(end_pick_time - start_pick_time) AS successful_picks_duration
     FROM 
        execution_data_pick 
     WHERE 
        failure_state = 'succeeded'
        AND end_pick_time IS NOT NULL
     GROUP BY 
        task_id
    ) AS sp ON t.id = sp.task_id
LEFT JOIN 
    (SELECT 
        task_id, 
        COUNT(*) AS unsuccessful_pick_count 
     FROM 
        execution_data_pick 
     WHERE 
        failure_state <> 'succeeded'
     GROUP BY 
        task_id
    ) AS up ON t.id = up.task_id
GROUP BY 
    t.id, e.robot_id, first_pick.pick_object, e.description, sp.successful_pick_count, up.unsuccessful_pick_count, sp.successful_picks_duration;
    """
    )
    tasks_data = np.array(cur.fetchall())

    # Fetch robots
    cur.execute(
        """
        SELECT * FROM execution_data_robot;
        """
    )
    robots_data = np.array(cur.fetchall())

    cur.execute(
        """
        SELECT DISTINCT description FROM execution_data_experiment;
        """
    )
    sites_data = np.array(cur.fetchall())

    cur.execute(
        """
        SELECT DISTINCT pick_object FROM execution_data_pick; 
        """
    )
    objects_data = np.array(cur.fetchall())

    destinations_data = np.array(
        [
            {
                "robot_id": "19cfa72e-ce93-49df-8b6e-62da5837f0e1",
                "name": "P-KUKA-COCO-000001",
                "address": "192.168.195.250",
                "last_sync": "never",
            },
            {
                "robot_id": "cf810af6-53be-4edf-b143-bd1565782f01",
                "name": "P-KUKA-COCO-000003",
                "address": "192.168.195.121",
                "last_sync": "never",
            },
                        {
                "robot_id": "3eedc3fd-8efc-4c4f-b351-6843d79689bf",
                "name": "P-KUKA-COCO-000006",
                "address": "192.168.195.107",
                "last_sync": "never",
            },
        ]
    )
    yield
    # Close the cursor and connection
    cur.close()
    conn.close()


app = FastAPI(lifespan=lifespan)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def filter_picks_data(lowerbound_dt, upperbound_dt, robot_id, site, pick_object):
    # Timezone conversion
    lowerbound_dt_utc = np.datetime64(lowerbound_dt.astimezone(timezone.utc))
    upperbound_dt_utc = np.datetime64(upperbound_dt.astimezone(timezone.utc))

    # Data filtering
    filtered_data = picks_data[
        (picks_data[:, 0] >= lowerbound_dt_utc)
        & (picks_data[:, 0] <= upperbound_dt_utc)
    ]
    if robot_id != "all":
        filtered_data = filtered_data[filtered_data[:, 3] == robot_id]
    if site != "all":
        filtered_data = filtered_data[filtered_data[:, 5] == site]
    if pick_object != "all":
        filtered_data = filtered_data[filtered_data[:, 1] == pick_object]

    return filtered_data


def filter_tasks_data(lowerbound_dt, upperbound_dt, robot_id, site, pick_object):
    # Timezone conversion
    lowerbound_dt_utc = np.datetime64(lowerbound_dt.astimezone(timezone.utc))
    upperbound_dt_utc = np.datetime64(upperbound_dt.astimezone(timezone.utc))

    # Data filtering
    filtered_data = tasks_data[
        (tasks_data[:, 6] >= lowerbound_dt_utc)
        & (tasks_data[:, 6] <= upperbound_dt_utc)
    ]
    if robot_id != "all":
        filtered_data = filtered_data[filtered_data[:, 8] == robot_id]
    if site != "all":
        filtered_data = filtered_data[filtered_data[:, 9] == site]
    if pick_object != "all":
        filtered_data = filtered_data[filtered_data[:, 0] == pick_object]

    return filtered_data


def generate_intervals(interval, filtered_data):
    intervals = {"daily": "D", "weekly": "W", "monthly": "M"}
    date_interval = intervals[interval]
    dates = np.array(
        [
            np.datetime64(dt).astype(f"datetime64[{date_interval}]")
            for dt in filtered_data[:, 0]
        ]
    )
    unique_intervals = np.unique(dates)

    return dates, unique_intervals


@app.get("/picks")
async def read_mpph(
    lowerbound_dt: datetime,
    upperbound_dt: datetime,
    interval: str,
    robot_id: str = "all",
    site: str = "all",
    pick_object: str = "all",
):
    # Validate interval input
    if interval not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid interval. Choose from 'daily', 'weekly', 'monthly'.",
        )

    filtered_data = filter_picks_data(
        lowerbound_dt, upperbound_dt, robot_id, site, pick_object
    )

    # Grouping by intervals
    dates, unique_intervals = generate_intervals(interval, filtered_data)

    # Calculate MPPH,
    result = []
    weights_of_pick_objects = {
        "zucchini": 200,  # weight in grams
        "avocado": 100,  # weight in grams
    }
    accumulated_tonnes = 0.0
    accumulated_total_duration = 0
    accumulated_picks = 0
    for period in unique_intervals:
        period_data = filtered_data[dates == period]
        total_weight = 0
        for row in period_data:
            pick_weight = weights_of_pick_objects.get(
                row[1], 150
            )  # Default weight if not found
            total_weight += pick_weight

        average_pph = np.mean(period_data[:, 4].astype(np.integer))
        total_weight_tonnes = total_weight / 1_000_000  # Convert grams to tonnes
        accumulated_tonnes += total_weight_tonnes  # Update accumulated tonnes

        total_duration = np.sum(period_data[:, 2].astype(np.integer))
        accumulated_total_duration += total_duration  # Update accumulated duration

        total_picks = np.count_nonzero(period_data[:, 4])
        accumulated_picks += total_picks  # Update accumulated picks

        result.append(
            {
                "date": str(period),
                "mpph": round(average_pph),
                "total_duration": int(total_duration),
                "total_picks": int(total_picks),
                "tonnes": float(f"{total_weight_tonnes:.3f}"),
                "accumulated_total_duration": int(accumulated_total_duration),
                "accumulated_picks": int(accumulated_picks),
                "accumulated_tonnes": float(f"{accumulated_tonnes:.3f}"),
            }
        )

    # Initialize lists to store values for each field
    mpph_values = []
    total_duration_values = []
    total_picks_values = []
    tonnes_values = []
    accumulated_total_duration_values = []
    accumulated_picks_values = []
    accumulated_tonnes_values = []

    # Populate the lists with values from each entry in the result
    for entry in result:
        mpph_values.append(entry["mpph"])
        total_duration_values.append(entry["total_duration"])
        total_picks_values.append(entry["total_picks"])
        tonnes_values.append(entry["tonnes"])
        accumulated_total_duration_values.append(entry["accumulated_total_duration"])
        accumulated_picks_values.append(entry["accumulated_picks"])
        accumulated_tonnes_values.append(entry["accumulated_tonnes"])

    # Calculate min and max for each field
    min_mpph = min(mpph_values, default=0)
    max_mpph = max(mpph_values, default=0)
    min_total_duration = min(total_duration_values, default=0)
    max_total_duration = max(total_duration_values, default=0)
    min_total_picks = min(total_picks_values, default=0)
    max_total_picks = max(total_picks_values, default=0)
    min_tonnes = min(tonnes_values, default=0.0)
    max_tonnes = max(tonnes_values, default=0.0)
    min_accumulated_total_duration = min(accumulated_total_duration_values, default=0)
    max_accumulated_total_duration = max(accumulated_total_duration_values, default=0)
    min_accumulated_picks = min(accumulated_picks_values, default=0)
    max_accumulated_picks = max(accumulated_picks_values, default=0)
    min_accumulated_tonnes = min(accumulated_tonnes_values, default=0.0)
    max_accumulated_tonnes = max(accumulated_tonnes_values, default=0.0)

    # Return result with min and max values
    return {
        "series": result,
        "min_mpph": min_mpph,
        "max_mpph": max_mpph,
        "min_total_duration": min_total_duration,
        "max_total_duration": max_total_duration,
        "min_total_picks": min_total_picks,
        "max_total_picks": max_total_picks,
        "min_tonnes": min_tonnes,
        "max_tonnes": max_tonnes,
        "min_accumulated_total_duration": min_accumulated_total_duration,
        "max_accumulated_total_duration": max_accumulated_total_duration,
        "min_accumulated_picks": min_accumulated_picks,
        "max_accumulated_picks": max_accumulated_picks,
        "min_accumulated_tonnes": min_accumulated_tonnes,
        "max_accumulated_tonnes": max_accumulated_tonnes,
    }


@app.get("/tasks")
async def read_tasks(
    lowerbound_dt: datetime,
    upperbound_dt: datetime,
    interval: str,
    robot_id: str = "all",
    site: str = "all",
    pick_object: str = "all",
):
    # Validate interval input
    if interval not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid interval. Choose from 'daily', 'weekly', 'monthly'.",
        )

    filtered_data = filter_tasks_data(
        lowerbound_dt, upperbound_dt, robot_id, site, pick_object
    )

    # Assuming start_date is in the 6th column (index 5) of tasks_data
    interval_format = {"daily": "D", "weekly": "W", "monthly": "M"}
    date_interval = interval_format[interval]
    dates = np.array(
        [
            np.datetime64(dt).astype(f"datetime64[{date_interval}]")
            for dt in filtered_data[:, 6]
        ]
    )
    unique_intervals = np.unique(dates)

    def safe_float(value, precision=2):
        """Safely convert to float and round to avoid JSON serialization issues."""
        try:
            return round(float(value), precision)
        except (ValueError, TypeError):
            return 0.0

    result = []
    accumulating_total_tasks = 0
    accumulating_total_duration = 0.0
    accumulating_total_successful_picks_duration = 0.0
    accumulating_total_successful_pick_count = 0
    accumulating_total_unsuccessful_pick_count = 0
    for period in unique_intervals:
        period_data = filtered_data[dates == period]

        total_tasks = len(period_data)
        accumulating_total_tasks += total_tasks
        total_duration = safe_float(np.nansum(period_data[:, 2].astype(np.float64)))
        accumulating_total_duration += total_duration
        total_successful_picks_duration = safe_float(
            np.nansum(period_data[:, 3].astype(np.float64))
        )
        accumulating_total_successful_picks_duration += total_successful_picks_duration
        total_successful_pick_count = int(
            np.nansum(period_data[:, 4].astype(np.integer))
        )
        accumulating_total_successful_pick_count += total_successful_pick_count
        total_unsuccessful_pick_count = int(
            np.nansum(period_data[:, 5].astype(np.integer))
        )
        accumulating_total_unsuccessful_pick_count += total_unsuccessful_pick_count

        result.append(
            {
                "date": str(period),
                "total_tasks": int(total_tasks),
                "total_duration": int(total_duration),
                "total_successful_picks_duration": int(total_successful_picks_duration),
                "total_successful_pick_count": int(total_successful_pick_count),
                "total_unsuccessful_pick_count": int(total_unsuccessful_pick_count),
                "accumulating_total_tasks": int(accumulating_total_tasks),
                "accumulating_total_duration": int(accumulating_total_duration),
                "accumulating_total_successful_picks_duration": int(
                    accumulating_total_successful_picks_duration
                ),
                "accumulating_total_successful_pick_count": int(
                    accumulating_total_successful_pick_count
                ),
                "accumulating_total_unsuccessful_pick_count": int(
                    accumulating_total_unsuccessful_pick_count
                ),
            }
        )
        # Extract values for each field into separate lists
        total_tasks_values = [entry["total_tasks"] for entry in result]
        total_duration_values = [entry["total_duration"] for entry in result]
        total_successful_picks_duration_values = [
            entry["total_successful_picks_duration"] for entry in result
        ]
        total_successful_pick_count_values = [
            entry["total_successful_pick_count"] for entry in result
        ]
        total_unsuccessful_pick_count_values = [
            entry["total_unsuccessful_pick_count"] for entry in result
        ]
        accumulating_total_tasks_values = [
            entry["accumulating_total_tasks"] for entry in result
        ]
        accumulating_total_duration_values = [
            entry["accumulating_total_duration"] for entry in result
        ]
        accumulating_total_successful_picks_duration_values = [
            entry["accumulating_total_successful_picks_duration"] for entry in result
        ]
        accumulating_total_successful_pick_count_values = [
            entry["accumulating_total_successful_pick_count"] for entry in result
        ]
        accumulating_total_unsuccessful_pick_count_values = [
            entry["accumulating_total_unsuccessful_pick_count"] for entry in result
        ]

        # Calculate min and max for each field
        min_total_tasks = min(total_tasks_values, default=0)
        max_total_tasks = max(total_tasks_values, default=0)
        min_total_duration = min(total_duration_values, default=0)
        max_total_duration = max(total_duration_values, default=0)
        min_total_successful_picks_duration = min(
            total_successful_picks_duration_values, default=0
        )
        max_total_successful_picks_duration = max(
            total_successful_picks_duration_values, default=0
        )
        min_total_successful_pick_count = min(
            total_successful_pick_count_values, default=0
        )
        max_total_successful_pick_count = max(
            total_successful_pick_count_values, default=0
        )
        min_total_unsuccessful_pick_count = min(
            total_unsuccessful_pick_count_values, default=0
        )
        max_total_unsuccessful_pick_count = max(
            total_unsuccessful_pick_count_values, default=0
        )
        min_accumulating_total_tasks = min(accumulating_total_tasks_values, default=0)
        max_accumulating_total_tasks = max(accumulating_total_tasks_values, default=0)
        min_accumulating_total_duration = min(
            accumulating_total_duration_values, default=0
        )
        max_accumulating_total_duration = max(
            accumulating_total_duration_values, default=0
        )
        min_accumulating_total_successful_picks_duration = min(
            accumulating_total_successful_picks_duration_values, default=0
        )
        max_accumulating_total_successful_picks_duration = max(
            accumulating_total_successful_picks_duration_values, default=0
        )
        min_accumulating_total_successful_pick_count = min(
            accumulating_total_successful_pick_count_values, default=0
        )
        max_accumulating_total_successful_pick_count = max(
            accumulating_total_successful_pick_count_values, default=0
        )

    # Return result with min and max values
    return {
        "series": result,
        "min_total_tasks": min_total_tasks,
        "max_total_tasks": max_total_tasks,
        "min_total_duration": min_total_duration,
        "max_total_duration": max_total_duration,
        "min_total_successful_picks_duration": min_total_successful_picks_duration,
        "max_total_successful_picks_duration": max_total_successful_picks_duration,
        "min_total_successful_pick_count": min_total_successful_pick_count,
        "max_total_successful_pick_count": max_total_successful_pick_count,
        "min_total_unsuccessful_pick_count": min_total_unsuccessful_pick_count,
        "max_total_unsuccessful_pick_count": max_total_unsuccessful_pick_count,
        "min_accumulating_total_tasks": min_accumulating_total_tasks,
        "max_accumulating_total_tasks": max_accumulating_total_tasks,
        "min_accumulating_total_duration": min_accumulating_total_duration,
        "max_accumulating_total_duration": max_accumulating_total_duration,
        "min_accumulating_total_successful_picks_duration": min_accumulating_total_successful_picks_duration,
        "max_accumulating_total_successful_picks_duration": max_accumulating_total_successful_picks_duration,
        "min_accumulating_total_successful_pick_count": min_accumulating_total_successful_pick_count,
        "max_accumulating_total_successful_pick_count": max_accumulating_total_successful_pick_count,
    }


@app.get("/robots")
async def read_robots():
    robots_list = [{"id": robot[0], "name": robot[1]} for robot in robots_data]
    return {"robots": robots_list}


@app.get("/sites")
async def read_sites():
    sites_list = [site[0] for site in sites_data]
    return {"sites": sites_list}


@app.get("/objects")
async def read_objects():
    objects_list = [obj[0] for obj in objects_data]
    return {"objects": objects_list}


@app.get("/destinations")
async def read_destinations():
    # Add last sync end date to destinations data
    for destination in destinations_data:
        conn = psycopg2.connect(
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            host=PGHOST,
            port=PGPORT,
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT MAX(end_date) FROM sync_log WHERE robot_id = %s",
            (destination["robot_id"],),
        )
        last_sync_end_date = cur.fetchone()[0]
        if last_sync_end_date:
            destination["last_sync"] = last_sync_end_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            destination["last_sync"] = None
    return destinations_data.tolist()


@app.get("/sync")
async def sync(robot_id: str, address: str):
    try:
        conn = psycopg2.connect(
            dbname=PGDATABASE,
            user=PGUSER,
            password=PGPASSWORD,
            host=PGHOST,
            port=PGPORT,
        )
        cur = conn.cursor()

        # Check for the most recent end_date in sync_log for the given robot_id
        cur.execute(
            "SELECT MAX(end_date) FROM sync_log WHERE robot_id = %s AND status = 'success'",
            (robot_id,),
        )
        last_sync_end_date = cur.fetchone()[0]

        # Check if the admin server is reachable
        admin_url = f"http://{address}:8000/admin"
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.get(admin_url)

        # Set start_date to the most recent end_date from sync_log, if it exists
        if last_sync_end_date:
            start_date = last_sync_end_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Default start_date if no previous syncs found
            start_date = datetime(2018, 1, 1).strftime("%Y-%m-%d %H:%M:%S")

        end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Backup data request
        base_backup_url = f"http://{address}:8000/api/backup_data"
        backup_url = f"{base_backup_url}?start_date={start_date}&end_date={end_date}&robots={robot_id}"
        backup_response = requests.get(backup_url, timeout=3.001)

        if backup_response.status_code == 200:
            # Restore data request
            restore_url = "http://192.168.195.194:8000/api/restore_data"
            files = {
                "backup_file": (
                    "data.pickle",
                    backup_response.content,
                    "application/octet-stream",
                )
            }
            restore_response = requests.post(restore_url, files=files, timeout=10)

            if restore_response.status_code == 200:
                # Insert a new row to the sync_log table
                insert_query = """
                INSERT INTO sync_log (robot_id, address, start_date, end_date, status, message) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(
                    insert_query,
                    (
                        robot_id,
                        address,
                        start_date,
                        end_date,
                        "success",
                        "Sync completed successfully",
                    ),
                )
                conn.commit()

                return {"message": "success"}
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to restore data. Server responded with status code {restore_response.status_code}: {restore_response.text}",
                )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to backup data. Server responded with status code {backup_response.status_code}: {backup_response.text}",
            )

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail="Offline")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
