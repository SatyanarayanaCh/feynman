# 3-Qubit Clifford Circuit: Linear Subspace, Affine Coset & Quadratic Phase
# Prepares the Affine-shifted GHZ state: (|001> - |110>)/sqrt(2)
.v q0 q1 q2
.i q0 q1 q2

BEGIN
H q0
tof q0 q1
tof q1 q2
X q2
cz q0 q1
END
