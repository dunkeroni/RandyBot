import sqlite3
import datetime

class StatTracker:
    def __init__(self):
        self.users_conn = sqlite3.connect('users.db')
        self.users_cursor = self.users_conn.cursor()
        self.request_conn = sqlite3.connect('requests.db')
        self.request_cursor = self.request_conn.cursor()

        #users table has the following columns: user_id, total_points, replies, successful_requests, stars_given, stars_received
        self.users_cursor.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id text, total_points integer, replies integer, successful_requests integer, stars_given integer, stars_received integer)''')
        
        #daily table has the following columns: post_id, reply_id, type, user_id, timestamp, stars
        self.request_cursor.execute('''CREATE TABLE IF NOT EXISTS requests
                     (post_id text, reply_id text, type text, user_id text, timestamp text, stars integer)''')
        
        self.users_conn.commit()
        self.request_conn.commit()

    def add_user(self, user_id):
        self.users_cursor.execute("INSERT INTO users VALUES (?, 0, 0, 0, 0, 0)", (user_id,))
        self.users_conn.commit()

    def add_request(self, post_id, reply_id, type, user_id, timestamp, stars):
        self.request_cursor.execute("INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?)", (post_id, reply_id, type, user_id, timestamp, stars))
        self.request_conn.commit()

    def get_user(self, user_id):
        self.users_cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return self.users_cursor.fetchone()

    def get_total_users(self):
        self.users_cursor.execute("SELECT COUNT(*) FROM users")
        result = self.users_cursor.fetchone()
        return result[0]
    
    def get_daily(self, post_id):
        self.request_cursor.execute("SELECT * FROM requests WHERE post_id=?", (post_id,))
        return self.request_cursor.fetchone()
    
    def update_user(self, user_id, column, value):
        self.users_cursor.execute("UPDATE users SET " + column + "=? WHERE user_id=?", (value, user_id))
        self.users_conn.commit()

    def update_requests(self, post_id, column, value):
        self.request_cursor.execute("UPDATE requests SET " + column + "=? WHERE post_id=?", (value, post_id))
        self.request_conn.commit()
    
    def assign_points_for_reply(self, reference_id, reference_user, reply_id, reply_user):
        #At this point, both users exist and at least one id->id relationship in the requests table exists
        #Step 1: Count how many times this user has replied to this request
        self.request_cursor.execute("SELECT COUNT(*) FROM requests WHERE post_id=? AND user_id=?", (reference_id, reply_user[0]))
        result = self.request_cursor.fetchone()
        reply_count = result[0]
        if reply_count > 3:
            return
        if reply_count == 1:
            reply_points = 3
        else:
            reply_points = 1
            
        #step 2: Count how many unique user_id's have replied to this request
        self.request_cursor.execute("SELECT COUNT(DISTINCT user_id) FROM requests WHERE post_id=?", (reference_id,))
        result = self.request_cursor.fetchone()
        request_points = result[0]

        #Step 3: If more than one of the requests are fulfilled by this user_id already, set request_points to 0
        if reply_count > 1:
            request_points = 0 #This user has already fulfilled this request

        print(f"User reply count: {str(reply_count)}. Total replies: {str(request_points)}. Rewarding {str(reply_points)} points to {reply_user[0]} and {str(request_points)} points to {reference_user[0]}.")
        self.update_user(reply_user[0], "total_points", reply_user[1] + reply_points)
        self.update_user(reference_user[0], "total_points", reference_user[1] + request_points)


    def handle_new_reply(self, reference_user, reference_id, reply_user, reply_id, timestamp):
        reference = self.get_user(reference_user)
        reply = self.get_user(reply_user)
        if reference is None:
            self.add_user(reference_user)
            reference = self.get_user(reference_user)
        if reply is None:
            self.add_user(reply_user)
            reply = self.get_user(reply_user)
        self.update_user(reference_user, "successful_requests", reference[3] + 1)
        self.update_user(reply_user, "replies", reply[2] + 1)
        self.add_request(reference_id, reply_id, "reply", reply_user, timestamp, 0)
        self.assign_points_for_reply(reference_id, reference, reply_id, reply)

    def top_rankings(self):
        self.users_cursor.execute("SELECT * FROM users ORDER BY total_points DESC LIMIT 5")
        return self.users_cursor.fetchall()
    def top_users(self, timeframe="today"):
        """
        Get top 3 users by points earned in the given timeframe.
        timeframe: "today", "week", or "month"
        """

        now = datetime.datetime.now(datetime.timezone.utc)
        if timeframe == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "week":
            start = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError("Invalid timeframe")

        start_iso = start.date().isoformat()
        self.request_cursor.execute(
            "SELECT user_id, SUM(CASE WHEN type='reply' THEN 3 ELSE 0 END) as points "
            "FROM requests WHERE DATE(timestamp) >= ? GROUP BY user_id ORDER BY points DESC LIMIT 3",
            (start_iso,)
        )
        return self.request_cursor.fetchall()

    def top_requests(self, timeframe="today"):
        """
        Get top 3 requests (post_id) by number of replies in the given timeframe.
        timeframe: "today", "week", or "month"
        """

        now = datetime.datetime.now(datetime.timezone.utc)
        if timeframe == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "week":
            start = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError("Invalid timeframe")

        start_iso = start.date().isoformat()
        self.request_cursor.execute(
            "SELECT post_id, COUNT(*) as reply_count "
            "FROM requests WHERE type='reply' AND DATE(timestamp) >= ? "
            "GROUP BY post_id ORDER BY reply_count DESC LIMIT 3",
            (start_iso,)
        )
        return self.request_cursor.fetchall()