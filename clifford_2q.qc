# 2-Qubit Clifford Circuit: Linear Parity & Affine Shift
# Prepares the Singlet Bell state: |Psi-> = (|01> - |10>)/sqrt(2)
.v q0 q1
.i q0 q1

BEGIN
H q0
cnot q0 q1
X q1
Z q0
END
