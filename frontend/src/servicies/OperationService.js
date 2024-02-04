import axios from "axios";

const API_URL = "api/";

class OperationService {
  getForTech(accessToken) {
    return axios.get(API_URL + 'operations_for_tech/', {
      headers: { 'Authorization': 'Bearer ' + String(accessToken) }
    });
  }
}

const operationService = new OperationService();
export default operationService;
