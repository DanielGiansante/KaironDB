package main

/*
#include <stdlib.h>

// Assinatura da callback que espera o resultado e o ID da requisição
typedef void (*QueryResultCallback)(char* result, char* request_id);

static inline void invoke_callback(QueryResultCallback cb, char* result, char* request_id) {
    cb(result, request_id);
}
*/
import "C"
import (
	"encoding/json"
	"fmt"
	"unsafe"

	_ "github.com/denisenkom/go-mssqldb"
	_ "github.com/go-sql-driver/mysql"
	_ "github.com/lib/pq"
	_ "github.com/mattn/go-sqlite3"
)

//export CreatePool
func CreatePool(connParamsJSON *C.char) *C.char {
	var connParams ConnectionParams
	if err := json.Unmarshal([]byte(C.GoString(connParamsJSON)), &connParams); err != nil {
		return C.CString(fmt.Sprintf(`{"error":"JSON de conexão inválido: %v"}`, err))
	}
	poolID, err := globalPoolManager.Create(connParams)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"falha ao criar pool: %v"}`, err))
	}
	return C.CString(poolID)
}

//export ClosePool
func ClosePool(poolID *C.char) *C.char {
	err := globalPoolManager.Close(C.GoString(poolID))
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"falha ao fechar pool: %v"}`, err))
	}
	return C.CString(`{"status":"success"}`)
}

//export BeginTransaction
func BeginTransaction(poolID *C.char) *C.char {
	db, found := globalPoolManager.Get(C.GoString(poolID))
	if !found {
		return C.CString(fmt.Sprintf(`{"error":"pool com ID %s não encontrado"}`, C.GoString(poolID)))
	}
	txID, err := txManager.Begin(db)
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"falha ao iniciar transação: %v"}`, err))
	}
	return C.CString(txID)
}

//export CommitTransaction
func CommitTransaction(txID *C.char) *C.char {
	err := txManager.Commit(C.GoString(txID))
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"falha ao commitar transação: %v"}`, err))
	}
	return C.CString(`{"status":"success"}`)
}

//export RollbackTransaction
func RollbackTransaction(txID *C.char) *C.char {
	err := txManager.Rollback(C.GoString(txID))
	if err != nil {
		return C.CString(fmt.Sprintf(`{"error":"falha ao reverter transação: %v"}`, err))
	}
	return C.CString(`{"status":"success"}`)
}

//export ExecuteSQL_async
func ExecuteSQL_async(poolID *C.char, query *C.char, txID *C.char, callback C.QueryResultCallback, requestID *C.char) {
	go func() {
		result := executeSQLSync(poolID, query, txID)
		C.invoke_callback(callback, result, requestID)
	}()
}

func executeSQLSync(poolID_c *C.char, query_c *C.char, txID_c *C.char) *C.char {
	reqJSON := C.GoString(query_c)
	var req Request
	if err := json.Unmarshal([]byte(reqJSON), &req); err != nil {
		return C.CString(fmt.Sprintf(`{"error": "JSON da requisição inválido: %s"}`, err.Error()))
	}
	poolIDStr := C.GoString(poolID_c)
	transactionID := C.GoString(txID_c)

	if transactionID != "" {
		entry, found := txManager.Get(transactionID)
		if !found {
			return C.CString(fmt.Sprintf(`{"error":"transação com ID %s não encontrada"}`, transactionID))
		}
		switch req.Operation {
		case "select":
			return runSelect(entry.tx, req)
		case "update":
			return runUpdate(entry.tx, req)
		case "delete":
			return runDelete(entry.tx, req)
		case "exec":
			return runExec(entry.tx, req)
		}
	} else {
		db, found := globalPoolManager.Get(poolIDStr)
		if !found {
			return C.CString(fmt.Sprintf(`{"error":"pool com ID %s não encontrado"}`, poolIDStr))
		}
		switch req.Operation {
		case "select":
			return runSelect(db, req)
		case "update":
			return runUpdate(db, req)
		case "delete":
			return runDelete(db, req)
		case "exec":
			return runExec(db, req)
		}
	}
	return C.CString(`{"error":"operação inválida ou não especificada"}`)
}

func main() {}

//export FreeCString
func FreeCString(p *C.char) {
	C.free(unsafe.Pointer(p))
}
