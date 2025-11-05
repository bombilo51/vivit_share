from decimal import Decimal

from app.models import Trip
def compute_net_balances(trip: Trip):
    """
    Returns two lists: creditors and debtors.
    Each item: (user_id, Decimal(amount))
    creditors: amount > 0 (should receive money)
    debtors: amount < 0 (owes money)
    """
    bal = trip.balances()  # {user_id: Decimal}
    creditors = []
    debtors = []
    for uid, v in bal.items():
        if v > 0:
            creditors.append((uid, v))
        elif v < 0:
            debtors.append((uid, -v))  # store positive owed amount
    # sort creditors and debtors for deterministic settling (largest first)
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    return creditors, debtors


def minimize_transactions(creditors, debtors):
    """
    Greedy algorithm to produce a minimal set of payments: returns list of (from_user, to_user, amount)
    """
    i = j = 0
    payments = []
    while i < len(debtors) and j < len(creditors):
        debtor_id, owe_amt = debtors[i]
        creditor_id, recv_amt = creditors[j]
        pay = min(owe_amt, recv_amt)
        payments.append((debtor_id, creditor_id, pay))
        owe_amt -= pay
        recv_amt -= pay
        if owe_amt == 0:
            i += 1
        else:
            debtors[i] = (debtor_id, owe_amt)
        if recv_amt == 0:
            j += 1
        else:
            creditors[j] = (creditor_id, recv_amt)
    return payments