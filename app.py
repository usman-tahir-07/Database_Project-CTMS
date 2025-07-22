from flask import Flask, render_template, request, redirect, url_for
from db_config import get_db_connection

app = Flask(__name__)

@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Tournament")
    tournament_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Team")
    team_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Player")
    player_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Match")
    match_count = cursor.fetchone()[0]

    conn.close()
    return render_template('home.html',
                           tournament_count=tournament_count,
                           team_count=team_count,
                           player_count=player_count,
                           match_count=match_count)

@app.route('/tournaments')
def view_tournaments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tournament")
    tournaments = cursor.fetchall()
    conn.close()
    return render_template('tournaments.html', tournaments=tournaments)

@app.route('/teams')
def view_teams():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.team_id, t.name, t.coach, t.captain, t.home_ground, tr.name AS tournament_name
        FROM Team t
        JOIN Tournament tr ON t.tournament_id = tr.tournament_id
    """)
    teams = cursor.fetchall()
    conn.close()
    return render_template('teams.html', teams=teams)


@app.route('/players', methods=['GET', 'POST'])
def view_players():
    conn = get_db_connection()
    cursor = conn.cursor()

    role_filter = request.form.get('role') if request.method == 'POST' else None
    nationality_filter = request.form.get('nationality') if request.method == 'POST' else None

    query = """
        SELECT p.player_id, p.name, p.dob, p.nationality, p.role,
               p.batting_style, p.bowling_style, t.name AS team_name
        FROM Player p
        JOIN Team t ON p.team_id = t.team_id
    """
    conditions = []
    params = []

    if role_filter:
        conditions.append("p.role = ?")
        params.append(role_filter)
    if nationality_filter:
        conditions.append("p.nationality = ?")
        params.append(nationality_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    players = cursor.fetchall()

    # Get unique roles and nationalities for dropdowns
    cursor.execute("SELECT DISTINCT role FROM Player")
    roles = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT nationality FROM Player")
    nationalities = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template('players.html',
                           players=players,
                           roles=roles,
                           nationalities=nationalities)


@app.route('/matches')
def view_matches():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.match_id, m.date, m.result,
               t1.name AS team1_name,
               t2.name AS team2_name,
               win.name AS winner_name,
               v.name AS venue_name,
               tr.name AS tournament_name
        FROM Match m
        JOIN Team t1 ON m.team1_id = t1.team_id
        JOIN Team t2 ON m.team2_id = t2.team_id
        LEFT JOIN Team win ON m.winner_id = win.team_id
        JOIN Venue v ON m.venue_id = v.venue_id
        JOIN Tournament tr ON m.tournament_id = tr.tournament_id
    """)
    matches = cursor.fetchall()
    conn.close()
    return render_template('matches.html', matches=matches)

@app.route('/performances')
def view_performances():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT M.match_id, P.name, F.runs_scored, F.balls_faced,
               F.wickets_taken, F.balls_bowled, F.overs_bowled
        FROM Performance F
        JOIN Match M ON F.match_id = M.match_id
        JOIN Player P ON F.player_id = P.player_id
    """)
    performances = [
        {
            'match': f"Match {row[0]}",
            'player': row[1],
            'runs_scored': row[2],
            'balls_faced': row[3],
            'wickets_taken': row[4],
            'balls_bowled': row[5],
            'overs_bowled': row[6]
        }
        for row in cursor.fetchall()
    ]
    return render_template('performance.html', performances=performances)

@app.route('/view_venue')
def view_venue():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Venue")
    venues = cursor.fetchall()
    return render_template('view_venue.html', venues=venues)

@app.route('/view_umpire')
def view_umpire():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Umpire")
    umpires = cursor.fetchall()
    return render_template('view_umpire.html', umpires=umpires)


@app.route('/add_tournament', methods=['GET', 'POST'])
def add_tournament():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        location = request.form['location']
        format_ = request.form['format']

        cursor.execute("""
            INSERT INTO Tournament (name, start_date, end_date, location, format)
            VALUES (?, ?, ?, ?, ?)
        """, (name, start_date, end_date, location, format_))
        conn.commit()
        return redirect(url_for('home'))
    return render_template('add_tournament.html')

@app.route('/add_venue', methods=['GET', 'POST'])
def add_venue():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        country = request.form['country']
        capacity = request.form['capacity']
        pitch_type = request.form['pitch_type']
        is_floodlit = 1 if 'is_floodlit' in request.form else 0

        cursor.execute("""
            INSERT INTO Venue (name, city, country, capacity, pitch_type, is_floodlit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, city, country, capacity, pitch_type, is_floodlit))
        conn.commit()
        return redirect(url_for('home'))
    return render_template('add_venue.html')

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        nationality = request.form['nationality']
        role = request.form['role']
        batting_style = request.form['batting_style']
        bowling_style = request.form['bowling_style']
        team_id = request.form['team_id']

        cursor.execute("""
            INSERT INTO Player (name, dob, nationality, role, batting_style, bowling_style, team_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, dob, nationality, role, batting_style, bowling_style, team_id))

        conn.commit()
        conn.close()
        return redirect(url_for('view_players'))  # Redirects to players listing

    # For GET: get all teams for the dropdown
    cursor.execute("SELECT team_id, name FROM Team")
    teams = cursor.fetchall()
    conn.close()

    return render_template('add_player.html', teams=teams)


@app.route('/add_match', methods=['GET', 'POST'])
def add_match():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        tournament_id = request.form['tournament_id']
        date = request.form['date']
        venue_id = request.form['venue_id']
        team1_id = request.form['team1_id']
        team2_id = request.form['team2_id']
        winner_id = request.form.get('winner_id') or None  # winner may be optional
        result = request.form['result']

        cursor.execute("""
            INSERT INTO Match (tournament_id, date, venue_id, team1_id, team2_id, winner_id, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tournament_id, date, venue_id, team1_id, team2_id, winner_id, result))

        conn.commit()
        conn.close()
        return redirect(url_for('view_matches'))

    # GET request: Load dropdown data
    cursor.execute("SELECT tournament_id, name FROM Tournament")
    tournaments = cursor.fetchall()

    cursor.execute("SELECT team_id, name FROM Team")
    teams = cursor.fetchall()

    cursor.execute("SELECT venue_id, name FROM Venue")
    venues = cursor.fetchall()

    conn.close()
    return render_template("add_match.html", tournaments=tournaments, teams=teams, venues=venues)

@app.route('/add_team', methods=['GET', 'POST'])
def add_team():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        coach = request.form['coach']
        captain = request.form['captain']
        home_ground = request.form['home_ground']
        tournament_id = request.form['tournament_id']

        cursor.execute("""
            INSERT INTO Team (name, coach, captain, home_ground, tournament_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, coach, captain, home_ground, tournament_id))

        conn.commit()
        conn.close()
        return redirect(url_for('view_teams'))  # or redirect to a teams list later

    # GET method — fetch tournaments for dropdown
    cursor.execute("SELECT tournament_id, name FROM Tournament")
    tournaments = cursor.fetchall()
    conn.close()

    return render_template("add_team.html", tournaments=tournaments)

@app.route('/add_umpire', methods=['GET', 'POST'])
def add_umpire():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        nationality = request.form['nationality']
        experience_years = request.form['experience_years']
        umpire_type = request.form['umpire_type']
        matches_officiated = request.form['matches_officiated']

        cursor.execute("""
            INSERT INTO Umpire (name, nationality, experience_years, umpire_type, matches_officiated)
            VALUES (?, ?, ?, ?, ?)
        """, (name, nationality, experience_years, umpire_type, matches_officiated))

        conn.commit()
        conn.close()
        return redirect(url_for('view_umpire'))

    conn.close()
    return render_template('add_umpire.html')

@app.route('/add_performance', methods=['GET', 'POST'])
def add_performance():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        match_id = request.form['match_id']
        player_id = request.form['player_id']
        runs_scored = request.form['runs_scored']
        balls_faced = request.form['balls_faced']
        wickets_taken = request.form['wickets_taken']
        balls_bowled = request.form['balls_bowled']
        overs_bowled = request.form['overs_bowled']

        cursor.execute("""
            INSERT INTO Performance (match_id, player_id, runs_scored, balls_faced, wickets_taken, balls_bowled, overs_bowled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (match_id, player_id, runs_scored, balls_faced, wickets_taken, balls_bowled, overs_bowled))

        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    cursor.execute("SELECT match_id, date FROM Match")
    matches = cursor.fetchall()

    cursor.execute("SELECT player_id, name FROM Player")
    players = cursor.fetchall()

    conn.close()
    return render_template('add_performance.html', matches=matches, players=players)

@app.route('/assign_umpire', methods=['GET', 'POST'])
def assign_umpire():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        match_id = request.form['match_id']
        umpire_id = request.form['umpire_id']
        role = request.form['role']

        cursor.execute("""
            INSERT INTO Match_Umpire (match_id, umpire_id, role)
            VALUES (?, ?, ?)
        """, (match_id, umpire_id, role))

        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    cursor.execute("SELECT match_id, date FROM Match")
    matches = cursor.fetchall()

    cursor.execute("SELECT umpire_id, name FROM Umpire")
    umpires = cursor.fetchall()

    conn.close()
    return render_template('assign_umpire.html', matches=matches, umpires=umpires)

@app.route('/delete_team/<int:team_id>', methods=['GET'])
def delete_team(team_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Attempt to delete the team with the given ID
    cursor.execute("DELETE FROM Team WHERE team_id = ?", (team_id,))
    
    conn.commit()
    conn.close()

    return redirect(url_for('view_teams'))  # Ensure this matches your route for viewing teams

@app.route('/delete_venue/<int:venue_id>', methods=['POST'])
def delete_venue(venue_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Venue WHERE venue_id = ?", (venue_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error deleting venue:", e)
    finally:
        cursor.close()
    return redirect(url_for('view_venue'))

@app.route('/delete_umpire/<int:umpire_id>', methods=['POST'])
def delete_umpire(umpire_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Umpire WHERE umpire_id = ?", (umpire_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('view_umpire'))  # Adjust name if route differs

if __name__ == '__main__':
    app.run(debug=True)
