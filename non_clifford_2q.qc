# 2-Qubit Simple Non-Clifford Circuit
# Prepares an entangled state with non-Clifford T phase
.v q0 q1
.i q0 q1

BEGIN
H q0
cnot q0 q1
T q1
END
