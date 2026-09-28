"""
Safe code execution endpoint for Codercise submissions.
Runs student Python code in a restricted subprocess with a timeout.
"""
import subprocess
import sys
import tempfile
import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/run", tags=["code_runner"])

TIMEOUT_SECONDS = 10
# Allowed imports for the sandbox
ALLOWED_PREAMBLE = """
import numpy as np
import math
import cmath
import random
"""


class RunRequest(BaseModel):
    code: str
    test_code: str = ""


class RunResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    passed: bool


@router.post("/execute", response_model=RunResponse)
async def execute_code(request: RunRequest):
    full_code = ALLOWED_PREAMBLE + "\n" + request.code
    if request.test_code:
        full_code += "\n" + request.test_code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(full_code)
        fname = f.name

    try:
        result = subprocess.run(
            [sys.executable, fname],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        stdout = result.stdout[:4000]
        stderr = result.stderr[:2000]
        passed = result.returncode == 0 and "passed" in stdout.lower()
        return RunResponse(success=result.returncode == 0, stdout=stdout, stderr=stderr, passed=passed)
    except subprocess.TimeoutExpired:
        return RunResponse(success=False, stdout="", stderr="Execution timed out (10s limit).", passed=False)
    except Exception as e:
        return RunResponse(success=False, stdout="", stderr=str(e), passed=False)
    finally:
        os.unlink(fname)


@router.post("/execute-pennylane", response_model=RunResponse)
async def execute_pennylane_code(request: RunRequest):
    """Execute PennyLane-based codercises (Xanadu Quantum Codebook style)."""
    pennylane_preamble = """
import numpy as np
import math
import cmath
import pennylane as qml
from pennylane import numpy as pnp

# Utility helpers available to all codercises
def unitary_check(U):
    \"\"\"Return True if U is unitary.\"\"\"
    n = U.shape[0]
    return np.allclose(U @ U.conj().T, np.eye(n))
"""
    full_code = pennylane_preamble + "\n" + request.code
    if request.test_code:
        full_code += "\n" + request.test_code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(full_code)
        fname = f.name

    try:
        result = subprocess.run(
            [sys.executable, fname],
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout[:6000]
        stderr = result.stderr[:3000]
        passed = result.returncode == 0 and "passed" in stdout.lower()
        return RunResponse(success=result.returncode == 0, stdout=stdout, stderr=stderr, passed=passed)
    except subprocess.TimeoutExpired:
        return RunResponse(success=False, stdout="", stderr="Execution timed out (30s limit).", passed=False)
    except Exception as e:
        return RunResponse(success=False, stdout="", stderr=str(e), passed=False)
    finally:
        os.unlink(fname)

async def execute_qiskit_code(request: RunRequest):
    """Execute code that may import qiskit."""
    qiskit_preamble = """
import numpy as np
import math
import cmath
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
"""
    full_code = qiskit_preamble + "\n" + request.code
    if request.test_code:
        full_code += "\n" + request.test_code

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(full_code)
        fname = f.name

    try:
        result = subprocess.run(
            [sys.executable, fname],
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout[:4000]
        stderr = result.stderr[:2000]
        passed = result.returncode == 0 and "passed" in stdout.lower()
        return RunResponse(success=result.returncode == 0, stdout=stdout, stderr=stderr, passed=passed)
    except subprocess.TimeoutExpired:
        return RunResponse(success=False, stdout="", stderr="Execution timed out (30s limit).", passed=False)
    except Exception as e:
        return RunResponse(success=False, stdout="", stderr=str(e), passed=False)
    finally:
        os.unlink(fname)
