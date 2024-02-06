import axios from "axios";

const API_URL = "api/";

class OperationService {
  getForTech(accessToken) {
    return axios.get(API_URL + "operations_for_tech/", {
      headers: { "Authorization": "Bearer " + String(accessToken) }
    });
  }

  getOperationStatuses(accessToken) {
    return axios.get(API_URL + "operation_statuses/", {
      headers: { "Authorization": "Bearer " + String(accessToken) }
    });
  }

  setOperationStatus(accessToken, operation_id, status_id) {
    return axios.patch(API_URL + `operation/${operation_id}/`, { "status_id": status_id }, {
      headers: { "Authorization": "Bearer " + String(accessToken) }
    });
  }
}

const operationService = new OperationService();
export default operationService;
