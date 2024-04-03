import axios from "axios";

const API_URL = "api/";

class OperationService {
  getForTech(page) {
    return axios.get(API_URL + `operations-for-tech/?page=${page}`);
  }

  getForProduct(productId) {
    return axios.get(API_URL + `operations-for-product/${productId}`);
  }

  getForSchedule(userEmail, date) {
    return axios.get(API_URL + `operations-for-schedule/${userEmail}/${date}`);
  }

  getOperationStatuses() {
    return axios.get(API_URL + "operation-statuses/");
  }

  setOperationStatus(operation_id, status_id) {
    return axios.patch(API_URL + `operation/${operation_id}/`, { "status_id": status_id });
  }
}

const operationService = new OperationService();
export default operationService;
