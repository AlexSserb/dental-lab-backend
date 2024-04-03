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

  setOperationStatus(operationId, statusId) {
    return axios.patch(API_URL + `operation/${operationId}/`, { "statusId": statusId });
  }
}

const operationService = new OperationService();
export default operationService;
