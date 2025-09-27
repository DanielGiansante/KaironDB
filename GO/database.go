package main

import (
	"C"
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
)

func connect(params ConnectionParams) (*sql.DB, error) {
	var dsn string
	switch params.Driver {
	case "sqlserver":
		dsn = fmt.Sprintf("sqlserver://%s:%s@%s?database=%s", params.User, params.Password, params.Server, params.Name)
	case "mysql":
		dsn = fmt.Sprintf("%s:%s@tcp(%s)/%s", params.User, params.Password, params.Server, params.Name)
	case "postgres":
		dsn = fmt.Sprintf("host=%s user=%s password=%s dbname=%s sslmode=require", params.Server, params.User, params.Password, params.Name)
	case "sqlite3":
		dsn = params.Server
	default:
		return nil, fmt.Errorf("driver não suportado: %s", params.Driver)
	}
	return sql.Open(params.Driver, dsn)
}

func buildWhereClauseRecursive(node QueryNode, driver string, paramIndex int) (string, []interface{}, int) {
	if len(node.Children) == 0 {
		return "", []interface{}{}, paramIndex
	}
	var clauses []string
	var params []interface{}
	for _, child := range node.Children {
		if conn, ok := child["connector"].(string); ok {
			childChildren, _ := child["children"].([]interface{})
			var typedChildren []map[string]interface{}
			for _, item := range childChildren {
				if typedItem, ok := item.(map[string]interface{}); ok {
					typedChildren = append(typedChildren, typedItem)
				}
			}
			subNode := QueryNode{Connector: conn, Children: typedChildren}
			subClause, subParams, newIndex := buildWhereClauseRecursive(subNode, driver, paramIndex)
			paramIndex = newIndex
			if subClause != "" {
				clauses = append(clauses, "("+subClause+")")
				params = append(params, subParams...)
			}
		} else {
			for key, value := range child {
				parts := strings.SplitN(key, "__", 2)
				fieldName := parts[0]
				lookup := "eq"
				if len(parts) == 2 {
					lookup = strings.ToLower(parts[1])
				}
				clause, val, newIndex := buildCondition(fieldName, lookup, value, driver, paramIndex)
				paramIndex = newIndex
				if clause != "" {
					clauses = append(clauses, clause)
					if v, ok := val.([]interface{}); ok && lookup == "in" {
						params = append(params, v...)
					} else if val != nil {
						params = append(params, val)
					}
				}
			}
		}
	}
	return strings.Join(clauses, " "+node.Connector+" "), params, paramIndex
}

func buildCondition(field, lookup string, value interface{}, driver string, paramIndex int) (string, interface{}, int) {
	if lookup == "isnull" {
		isNull, ok := value.(bool)
		if !ok {
			return "", nil, paramIndex
		}
		if isNull {
			return fmt.Sprintf("%s IS NULL", field), nil, paramIndex
		}
		return fmt.Sprintf("%s IS NOT NULL", field), nil, paramIndex
	}
	paramIndex++
	placeholder := "?"
	if driver == "sqlserver" {
		placeholder = fmt.Sprintf("@p%d", paramIndex)
	}
	var operator string
	switch lookup {
	case "eq":
		operator = "="
	case "ne", "neq":
		operator = "<>"
	case "gt":
		operator = ">"
	case "gte":
		operator = ">="
	case "lt":
		operator = "<"
	case "lte":
		operator = "<="
	case "like", "contains":
		operator = "LIKE"
	case "in":
		valSlice, ok := value.([]interface{})
		if !ok || len(valSlice) == 0 {
			return "", nil, paramIndex - 1
		}
		var placeholders []string
		currentPIndex := paramIndex
		for i := 0; i < len(valSlice); i++ {
			p := "?"
			if driver == "sqlserver" {
				p = fmt.Sprintf("@p%d", currentPIndex)
			}
			placeholders = append(placeholders, p)
			if i < len(valSlice)-1 {
				currentPIndex++
			}
		}
		paramIndex = currentPIndex
		return fmt.Sprintf("%s IN (%s)", field, strings.Join(placeholders, ", ")), valSlice, paramIndex
	default:
		operator = "="
	}
	return fmt.Sprintf("%s %s %s", field, operator, placeholder), value, paramIndex
}

type queryRunner interface {
	Query(query string, args ...interface{}) (*sql.Rows, error)
	Exec(query string, args ...interface{}) (sql.Result, error)
}

func runSelect(runner queryRunner, req Request) *C.char {
	fields := strings.Join(req.Fields, ", ")
	query := fmt.Sprintf("SELECT %s FROM %s", fields, req.Table)
	whereClause, args, _ := buildWhereClauseRecursive(req.WhereQ, req.Driver, 0)
	if whereClause != "" {
		query += " WHERE " + whereClause
	}
	rows, err := runner.Query(query, args...)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error": "%s"}`, err.Error()))
	}
	defer rows.Close()
	return serializeRows(rows)
}

func runUpdate(runner queryRunner, req Request) *C.char {
	if len(req.Data) == 0 {
		return C.CString(`{"error": "update operation with no data"}`)
	}
	var setClauses []string
	var params []interface{}
	paramIndex := 1
	for key, value := range req.Data {
		p := "?"
		if req.Driver == "sqlserver" {
			p = fmt.Sprintf("@p%d", paramIndex)
		}
		setClauses = append(setClauses, fmt.Sprintf("%s = %s", key, p))
		params = append(params, value)
		paramIndex++
	}
	setClause := strings.Join(setClauses, ", ")
	whereClause, whereParams, _ := buildWhereClauseRecursive(req.WhereQ, req.Driver, paramIndex-1)
	params = append(params, whereParams...)
	query := fmt.Sprintf("UPDATE %s SET %s", req.Table, setClause)
	if whereClause != "" {
		query += " WHERE " + whereClause
	}
	res, err := runner.Exec(query, params...)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error": "%s"}`, err.Error()))
	}
	n, _ := res.RowsAffected()
	return C.CString(fmt.Sprintf(`{"rows_affected": %d}`, n))
}

func runDelete(runner queryRunner, req Request) *C.char {
	whereClause, whereParams, _ := buildWhereClauseRecursive(req.WhereQ, req.Driver, 0)
	if whereClause == "" {
		return C.CString(`{"error": "delete operation without a where clause is not allowed"}`)
	}
	query := fmt.Sprintf("DELETE FROM %s WHERE %s", req.Table, whereClause)
	res, err := runner.Exec(query, whereParams...)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error": "%s"}`, err.Error()))
	}
	n, _ := res.RowsAffected()
	return C.CString(fmt.Sprintf(`{"rows_affected": %d}`, n))
}

func runExec(runner queryRunner, req Request) *C.char {
	fmt.Printf("DEBUG: runExec called with ExpectResult=%v, SQL=%s\n", req.ExpectResult, req.SQL)

	if req.ExpectResult {
		fmt.Printf("DEBUG: Executing Query (ExpectResult=true)\n")
		rows, err := runner.Query(req.SQL, req.Params...)
		if err != nil {
			fmt.Printf("DEBUG: Query error: %v\n", err)
			return C.CString(fmt.Sprintf(`{"error": "%s"}`, err.Error()))
		}
		defer rows.Close()
		result := serializeRows(rows)
		fmt.Printf("DEBUG: Query result: %s\n", C.GoString(result))
		return result
	}

	fmt.Printf("DEBUG: Executing Exec (ExpectResult=false)\n")
	res, err := runner.Exec(req.SQL, req.Params...)
	if err != nil {
		fmt.Printf("DEBUG: Exec error: %v\n", err)
		return C.CString(fmt.Sprintf(`{"error": "%s"}`, err.Error()))
	}
	n, _ := res.RowsAffected()
	result := C.CString(fmt.Sprintf(`{"rows_affected": %d}`, n))
	fmt.Printf("DEBUG: Exec result: %s\n", C.GoString(result))
	return result
}

func serializeRows(rows *sql.Rows) *C.char {
	cols, _ := rows.Columns()
	results := []map[string]interface{}{}
	for rows.Next() {
		scanArgs := make([]interface{}, len(cols))
		valPtrs := make([]interface{}, len(cols))
		for i := range cols {
			valPtrs[i] = &scanArgs[i]
		}
		if err := rows.Scan(valPtrs...); err != nil {
			return C.CString(fmt.Sprintf(`{"error": "failed to scan row: %s"}`, err.Error()))
		}
		row := make(map[string]interface{})
		for i, col := range cols {
			if b, ok := scanArgs[i].([]byte); ok {
				row[col] = string(b)
			} else {
				row[col] = scanArgs[i]
			}
		}
		results = append(results, row)
	}
	jsonBytes, _ := json.Marshal(results)
	return C.CString(string(jsonBytes))
}
