import axios from "axios";

const API_URL = "api/operation_types/";

class OperationTypesService {
  getAll(accessToken) {
    return axios.get(API_URL, {
      headers: { 'Authorization': 'Bearer ' + String(accessToken) }
    });
  }

  postOperType(operType, accessToken) {
    return axios.get(API_URL, operType, {
      headers: { 'Authorization': 'Bearer ' + String(accessToken) }
    });
  }

  putOperType(operType, accessToken) {
    return axios.put(API_URL, operType, {
      headers: { 'Authorization': 'Bearer ' + String(accessToken) }
    });
  }

  deleteOperType(operType, accessToken) {
    return axios.delete(API_URL + `${operType.id}`, {
      headers: { 'Authorization': 'Bearer ' + String(accessToken) }
    });
  }
}

const operationTypesService = new OperationTypesService();
export default operationTypesService;
