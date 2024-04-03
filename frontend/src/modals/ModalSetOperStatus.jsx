import React, { useState } from 'react';
import {
  Button, Typography, Modal,
  Select, MenuItem,
  Stack, Box
} from '@mui/material';

import ToothMarks from '../components/ToothMarks';
import operationService from "../servicies/OperationService";

const style = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 550,
  bgcolor: 'background.paper',
  borderRadius: '8px',
  boxShadow: 24,
  p: 4,
};

const ModalSetOperStatus = ({ operation, page, operationStatuses, loadOperations }) => {
  const [open, setOpen] = useState(false);
  let [selectedOperationStatus, setSelectedOperationStatus] = useState(operation?.operationStatus?.name);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const handleSubmit = () => {
    const status = operationStatuses.find(operSt => operSt.value === selectedOperationStatus);

    operationService.setOperationStatus(operation.id, status?.key)
      .then(_ => { 
        loadOperations(page);
      })
      .catch(err => console.log(err));

    handleClose();
  }

  return (
    <div>
      <Button variant="contained" sx={{ marginBottom: 1 }} onClick={handleOpen}>
        Изменить статус операции
      </Button>
      <Modal
        open={open}
        onClose={handleClose}
      >
        <Box sx={style}>
          <Typography variant="h5" component="h5" sx={{
            textAlign: "center",
            marginBottom: 3
          }}>
            Изменение статуса операции
          </Typography>
          <Stack spacing={1}>
            <Typography>Статус операции</Typography>
            <Select
              onChange={e => setSelectedOperationStatus(e.target.value)}
              value={selectedOperationStatus}
            >
              {operationStatuses.map(operation => (
                <MenuItem value={operation.value}>{operation.value}</MenuItem>
              ))}
            </Select>
            <Button variant="contained" onClick={handleSubmit}>
              Сохранить
            </Button>
            <hr />
            <Typography variant="h6" component="h6" sx={{
              textAlign: "center",
              marginTop: 2
            }}>
              Информация
            </Typography>
            <hr />
            <Typography>Вид операции: {operation.operationType.name}</Typography>
            <Typography>
              Время выполнения: {operation.operationType.execTime.substring(0, 2)}:
              {operation.operationType.execTime.substring(3, 5)}
            </Typography>

            <Typography>Информация об изделии</Typography>
            <Typography>Вид: {operation.product.productType.name}</Typography>
            <Typography>Статус: {operation.product.productStatus.name}</Typography>
            <Typography>Количество: {operation.product.amount}</Typography>
            <Typography>Формула для изделия</Typography>
            <ToothMarks teethList={operation.product.teeth} />
          </Stack>
        </Box>
      </Modal>
    </div>
  );
}

export default ModalSetOperStatus;