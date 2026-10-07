from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)

from functools import wraps
import hashlib
import sys
import os

from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =========================================================
# DATABASE IMPORTS
# =========================================================

from database.database import (
    find_certificate,
    add_certificate,
    get_all_certificates,
    save_verification,
    get_verification_history
)


# =========================================================
# BLOCKCHAIN IMPORT
# =========================================================

from blockchain.blockchain import CertificateBlockchain


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = "academic-certificate-secret-key-change-later"


# =========================================================
# ADMIN LOGIN
# =========================================================

ADMIN_USERNAME = "admin"

ADMIN_PASSWORD_HASH = generate_password_hash(
    "admin123"
)


# =========================================================
# BLOCKCHAIN
# =========================================================

certificate_blockchain = CertificateBlockchain()


# =========================================================
# DEFAULT DEMO CERTIFICATE
# =========================================================

DEFAULT_CERTIFICATE_ID = "CERT001"

DEFAULT_CERTIFICATE_HASH = (
    "c7bae63b5bba3d192e0568bd65da6fbd8edbbbc9fa9f7549d85d721b72888782"
)


# Add CERT001 to blockchain if it does not already exist

if not certificate_blockchain.find_certificate(
    DEFAULT_CERTIFICATE_ID
):

    certificate_blockchain.add_certificate(
        DEFAULT_CERTIFICATE_ID,
        DEFAULT_CERTIFICATE_HASH
    )


# =========================================================
# LOGIN REQUIRED DECORATOR
# =========================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if not session.get("admin_logged_in"):

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return decorated_function


# =========================================================
# HOME / CERTIFICATE VERIFICATION PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# ADMIN LOGIN PAGE
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # -----------------------------------------------------
    # SHOW LOGIN PAGE
    # -----------------------------------------------------

    if request.method == "GET":

        if session.get("admin_logged_in"):

            return redirect(
                url_for("admin")
            )

        return render_template(
            "login.html"
        )


    # -----------------------------------------------------
    # PROCESS LOGIN
    # -----------------------------------------------------

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )


    if (
        username == ADMIN_USERNAME
        and check_password_hash(
            ADMIN_PASSWORD_HASH,
            password
        )
    ):

        session["admin_logged_in"] = True

        session["admin_username"] = username

        return jsonify({
            "success": True,
            "message": "Login successful."
        })


    return jsonify({
        "success": False,
        "message": "Invalid username or password."
    }), 401


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@login_required
def admin():

    return render_template(
        "admin.html"
    )


# =========================================================
# REGISTER CERTIFICATE
# =========================================================

@app.route(
    "/admin/register",
    methods=["POST"]
)
@login_required
def register_certificate():

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    student_name = request.form.get(
        "student_name",
        ""
    ).strip()

    certificate_id = request.form.get(
        "certificate_id",
        ""
    ).strip()

    university = request.form.get(
        "university",
        ""
    ).strip()

    certificate = request.files.get(
        "certificate"
    )


    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not student_name:

        return jsonify({
            "success": False,
            "message": "Student name is required."
        }), 400


    if not certificate_id:

        return jsonify({
            "success": False,
            "message": "Certificate ID is required."
        }), 400


    if not university:

        return jsonify({
            "success": False,
            "message": "University name is required."
        }), 400


    if not certificate:

        return jsonify({
            "success": False,
            "message": "Certificate file is required."
        }), 400


    # -----------------------------------------------------
    # PDF VALIDATION
    # -----------------------------------------------------

    filename = certificate.filename or ""

    if not filename.lower().endswith(".pdf"):

        return jsonify({
            "success": False,
            "message": "Only PDF certificates are allowed."
        }), 400


    # -----------------------------------------------------
    # CHECK DUPLICATE CERTIFICATE
    # -----------------------------------------------------

    existing_certificate = find_certificate(
        certificate_id
    )

    if existing_certificate:

        return jsonify({
            "success": False,
            "message": (
                "Certificate ID already exists."
            )
        }), 409


    # -----------------------------------------------------
    # READ FILE
    # -----------------------------------------------------

    file_data = certificate.read()


    if not file_data:

        return jsonify({
            "success": False,
            "message": "Uploaded certificate is empty."
        }), 400


    # -----------------------------------------------------
    # CHECK PDF SIGNATURE
    # -----------------------------------------------------

    if not file_data.startswith(b"%PDF"):

        return jsonify({
            "success": False,
            "message": (
                "Invalid PDF file."
            )
        }), 400


    # -----------------------------------------------------
    # GENERATE SHA-256 HASH
    # -----------------------------------------------------

    certificate_hash = hashlib.sha256(
        file_data
    ).hexdigest()


    # -----------------------------------------------------
    # SAVE TO DATABASE
    # -----------------------------------------------------

    database_added = add_certificate(

        student_name,

        certificate_id,

        university,

        certificate_hash

    )


    if not database_added:

        return jsonify({
            "success": False,
            "message": (
                "Certificate could not be added "
                "to the database."
            )
        }), 500


    # -----------------------------------------------------
    # ADD TO BLOCKCHAIN
    # -----------------------------------------------------

    blockchain_added = (
        certificate_blockchain.add_certificate(
            certificate_id,
            certificate_hash
        )
    )


    if not blockchain_added:

        return jsonify({
            "success": False,
            "message": (
                "Certificate was saved in the "
                "database but could not be added "
                "to the blockchain."
            )
        }), 500


    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    return jsonify({

        "success": True,

        "message": (
            "Certificate registered successfully."
        ),

        "certificate_id": certificate_id,

        "certificate_hash": certificate_hash,

        "database": "Added to Database",

        "blockchain": "Added to Blockchain"

    })


# =========================================================
# VIEW ALL CERTIFICATES
# =========================================================

@app.route("/admin/certificates")
@login_required
def certificates():

    records = get_all_certificates()

    certificate_list = []


    for record in records:

        blockchain_record = (
            certificate_blockchain.find_certificate(
                record["certificate_id"]
            )
        )


        blockchain_match = False


        if blockchain_record:

            blockchain_match = (
                blockchain_record.certificate_hash
                == record["certificate_hash"]
            )


        certificate_list.append({

            "id": record["id"],

            "student_name":
                record["student_name"],

            "certificate_id":
                record["certificate_id"],

            "university":
                record["university"],

            "certificate_hash":
                record["certificate_hash"],

            "created_at":
                record["created_at"],

            "blockchain_match":
                blockchain_match

        })


    return render_template(

        "certificates.html",

        certificates=certificate_list,

        blockchain_valid=(
            certificate_blockchain.verify_chain()
        )

    )


# =========================================================
# VERIFICATION HISTORY
# =========================================================

@app.route("/admin/history")
@login_required
def verification_history():

    history = get_verification_history()

    history_list = []


    for record in history:

        history_list.append({

            "id": record["id"],

            "certificate_id":
                record["certificate_id"],

            "uploaded_hash":
                record["uploaded_hash"],

            "database_match":
                bool(record["database_match"]),

            "blockchain_match":
                bool(record["blockchain_match"]),

            "hash_match":
                bool(record["hash_match"]),

            "verification_status":
                record["verification_status"],

            "verified_at":
                record["verified_at"]

        })


    return render_template(

        "history.html",

        history=history_list

    )


# =========================================================
# VERIFY CERTIFICATE
# =========================================================

@app.route(
    "/verify",
    methods=["POST"]
)
def verify_certificate():

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

    certificate_id = request.form.get(
        "certificate_id",
        ""
    ).strip()

    student_name = request.form.get(
        "student_name",
        ""
    ).strip()

    university = request.form.get(
        "university",
        ""
    ).strip()

    certificate = request.files.get(
        "certificate"
    )


    # -----------------------------------------------------
    # BASIC FILE VALIDATION
    # -----------------------------------------------------

    if not certificate:

        return jsonify({
            "success": False,
            "message": "Certificate file is required."
        }), 400


    file_data = certificate.read()


    if not file_data:

        return jsonify({
            "success": False,
            "message": "Uploaded file is empty."
        }), 400


    # -----------------------------------------------------
    # GENERATE UPLOADED FILE HASH
    # -----------------------------------------------------

    uploaded_hash = hashlib.sha256(
        file_data
    ).hexdigest()


    # -----------------------------------------------------
    # FIND CERTIFICATE IN DATABASE
    # -----------------------------------------------------

    database_record = find_certificate(
        certificate_id
    )


    # -----------------------------------------------------
    # FIND CERTIFICATE IN BLOCKCHAIN
    # -----------------------------------------------------

    blockchain_record = (
        certificate_blockchain.find_certificate(
            certificate_id
        )
    )


    # -----------------------------------------------------
    # CHECK BLOCKCHAIN INTEGRITY
    # -----------------------------------------------------

    blockchain_integrity = (
        certificate_blockchain.verify_chain()
    )


    # -----------------------------------------------------
    # UNKNOWN CERTIFICATE
    # -----------------------------------------------------

    if not database_record:

        save_verification(

            certificate_id,

            uploaded_hash,

            False,

            False,

            False,

            "INVALID"

        )


        return jsonify({

            "success": False,

            "message": (
                "Certificate not found. "
                "This certificate is not registered."
            ),

            "certificate_id":
                certificate_id,

            "database_match":
                False,

            "blockchain_match":
                False,

            "hash_verified":
                False

        })


    # -----------------------------------------------------
    # DATABASE MATCH
    # -----------------------------------------------------

    database_match = True


    # -----------------------------------------------------
    # STUDENT NAME MATCH
    # -----------------------------------------------------

    student_match = (

        database_record["student_name"].strip().lower()
        == student_name.lower()

    )


    # -----------------------------------------------------
    # UNIVERSITY MATCH
    # -----------------------------------------------------

    university_match = (

        database_record["university"].strip().lower()
        == university.lower()

    )


    # -----------------------------------------------------
    # BLOCKCHAIN MATCH
    # -----------------------------------------------------

    blockchain_match = (

        blockchain_record is not None

        and blockchain_record.certificate_hash
        == database_record["certificate_hash"]

        and blockchain_integrity

    )


    # -----------------------------------------------------
    # HASH MATCH
    # -----------------------------------------------------

    hash_match = (

        uploaded_hash
        == database_record["certificate_hash"]

    )


    # -----------------------------------------------------
    # FINAL VALIDATION
    # -----------------------------------------------------

    certificate_valid = (

        database_match

        and student_match

        and university_match

        and blockchain_match

        and hash_match

    )


    # -----------------------------------------------------
    # SAVE VERIFICATION HISTORY
    # -----------------------------------------------------

    if certificate_valid:

        verification_status = "VALID"

    else:

        verification_status = "INVALID"


    save_verification(

        certificate_id,

        uploaded_hash,

        database_match,

        blockchain_match,

        hash_match,

        verification_status

    )


    # -----------------------------------------------------
    # INVALID CERTIFICATE
    # -----------------------------------------------------

    if not certificate_valid:

        return jsonify({

            "success": False,

            "message": (
                "Certificate verification failed."
            ),

            "certificate_id":
                certificate_id,

            "certificate_hash":
                uploaded_hash,

            "database_match":
                database_match,

            "student_match":
                student_match,

            "university_match":
                university_match,

            "blockchain_match":
                blockchain_match,

            "hash_verified":
                hash_match,

            "blockchain_integrity":
                blockchain_integrity

        })


    # -----------------------------------------------------
    # VALID CERTIFICATE
    # -----------------------------------------------------

    return jsonify({

        "success": True,

        "message": (
            "Certificate Verified Successfully"
        ),

        "certificate_id":
            certificate_id,

        "certificate_hash":
            uploaded_hash,

        "database_match":
            True,

        "student_match":
            True,

        "university_match":
            True,

        "blockchain_match":
            True,

        "hash_verified":
            True,

        "blockchain_integrity":
            True

    })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )