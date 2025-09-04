from lark import Lark, Transformer, Token
from django.db.models import Q

# ---------------- Grammar ----------------
saufql_grammar = r"""
    start: expr (order_by)?
    expr: condition (LOGIC condition)*

    ?condition: FIELD OP VALUE                -> condition_single
              | FIELD IN_OP "(" value_list ")" -> condition_in
              | NOT_OP condition               -> condition_not
              | "(" expr ")"                   -> group

    order_by: "ORDER" "BY" FIELD (DIRECTION)?

    value_list: VALUE ("," VALUE)*

    LOGIC: /(?i:AND|OR)/
    FIELD: /[a-zA-Z_][a-zA-Z0-9_]*/
    OP: "=" | "!=" | ">" | "<" | ">=" | "<=" | "~" | "!~"
    IN_OP: /(?i:IN|NOT IN)/
    NOT_OP: /(?i:NOT)/
    VALUE: ESCAPED_STRING | /[A-Za-z0-9_.]+/
    DIRECTION: /(?i:ASC|DESC)/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""

parser = Lark(saufql_grammar, parser="lalr")


# ---------------- Transformer (AST) ----------------
class ToAST(Transformer):
    def FIELD(self, tok: Token): return tok.value
    def OP(self, tok: Token): return tok.value.upper()
    def IN_OP(self, tok: Token): return tok.value.upper()
    def VALUE(self, tok: Token): return tok.value.strip('"')
    def DIRECTION(self, tok: Token): return tok.value.upper()
    def LOGIC(self, tok: Token): return tok.value.upper()
    def NOT_OP(self, tok: Token): return tok.value.upper()

    def start(self, items):
        ast = {"where": items[0]}
        if len(items) > 1 and isinstance(items[-1], dict) and "order_by" in items[-1]:
            ast["order_by"] = items[-1]["order_by"]
        return ast

    def expr(self, items):
        if len(items) == 1:
            return items[0]
        result = items[0]
        i = 1
        while i < len(items):
            logic = items[i]
            right = items[i + 1]
            result = {logic: [result, right]}
            i += 2
        return result

    def condition_single(self, items):
        return {"field": items[0], "op": items[1], "value": items[2]}

    def condition_in(self, items):
        return {"field": items[0], "op": items[1], "values": items[2]}

    def condition_not(self, items):
        return {"NOT": items[-1]}

    def group(self, items):
        return items[0]

    def value_list(self, items):
        return items

    def order_by(self, items):
        field = items[0]
        direction = items[1] if len(items) > 1 else "ASC"
        return {"order_by": ("-" if direction == "DESC" else "") + field}


# ---------------- AST -> Django ORM ----------------
def ast_to_django(ast, model_cls):
    if not ast:
        return None
    filters = build_filters(ast["where"])
    qs = model_cls.objects.filter(filters)
    if "order_by" in ast:
        qs = qs.order_by(ast["order_by"])
    return qs


def build_filters(node):
    """Recursively build Q objects from AST."""
    if isinstance(node, dict):
        if "field" in node:  # simple condition
            field, op = node["field"], node["op"]
            if op == "=":   return Q(**{field: node["value"]})
            if op == "!=":  return ~Q(**{field: node["value"]})
            if op == ">":   return Q(**{f"{field}__gt": node["value"]})
            if op == "<":   return Q(**{f"{field}__lt": node["value"]})
            if op == ">=":  return Q(**{f"{field}__gte": node["value"]})
            if op == "<=":  return Q(**{f"{field}__lte": node["value"]})
            if op == "~":   return Q(**{f"{field}__icontains": node["value"]})
            if op == "!~":  return ~Q(**{f"{field}__icontains": node["value"]})
            if op == "IN" or op == "in":  return Q(**{f"{field}__in": node["values"]})
            if op == "NOT IN" or op == "not in": return ~Q(**{f"{field}__in": node["values"]})
            raise ValueError(f"Unsupported operator {op}")

        elif "NOT" in node:
            return ~build_filters(node["NOT"])
        elif "AND" in node:
            left, right = node["AND"]
            return build_filters(left) & build_filters(right)
        elif "OR" in node:
            left, right = node["OR"]
            return build_filters(left) | build_filters(right)

    raise ValueError(f"Invalid AST node: {node}")


# ---------------- Example ----------------
def parse_query(query):
    try:
        tree = parser.parse(query)
        ast = ToAST().transform(tree)
        return ast
    except Exception as e:
        print("Query Parsing failed:", e)
        return None


if __name__ == "__main__":
    query = 'status not in ("Open", "Closed", "InProgress") and assignee = "kshitij.tyagi" ORDER BY priority DESC'
    ast = parse_query(query)
    print("AST:", ast)

    if ast:
        filters = build_filters(ast['where'])
        print("Filters:", filters)
    # Example: assume you have a Django model `Issue`
    # qs = ast_to_django(ast, Issue)
    # print(qs.query)   # prints generated SQL
