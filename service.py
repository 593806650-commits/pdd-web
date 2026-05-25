def analyze_products(products):

    total_profit = sum([p[3] for p in products])

    avg_profit = total_profit / len(products) if products else 0

    best = max(products, key=lambda x: x[3]) if products else None

    return {
        "total_profit": total_profit,
        "avg_profit": avg_profit,
        "best_product": best
    }