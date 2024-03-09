import axios from "axios";

const API_URL = "api/";

class OperationService {
  getForTech(page) {
    return axios.get(API_URL + `operations_for_tech/?page=${page}`);
  }

  getOperationStatuses() {
    return axios.get(API_URL + "operation_statuses/");
  }

  setOperationStatus(operation_id, status_id) {
    return axios.patch(API_URL + `operation/${operation_id}/`, { "status_id": status_id });
  }
}

const operationService = new OperationService();
export default operationService;
