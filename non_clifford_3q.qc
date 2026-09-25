# 3-Qubit Simple Non-Clifford Circuit
# Prepares a 3-qubit GHZ state with non-Clifford T phase
.v q0 q1 q2
.i q0 q1 q2

BEGIN
H q0
cnot q0 q1
cnot q1 q2
T q2
END
