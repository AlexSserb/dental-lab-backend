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

const ModalSetOperStatus = ({ oper, operStatuses, loadOperations }) => {
  const [open, setOpen] = useState(false);
  const [operation, setOperation] = useState(oper);
  const [operationStatuses, setOperationStatuses] = useState(operStatuses);
  let [selectedOperationStatus, setSelectedOperationStatus] = useState(oper?.operation_status?.name);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const handleSubmit = () => {
    const status = operStatuses.find(operSt => operSt.value === selectedOperationStatus);

    operationService.setOperationStatus(operation.id, status?.key)
      .then(res => { 
        loadOperations();
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
              {operationStatuses.map(oper => (
                <MenuItem value={oper.value}>{oper.value}</MenuItem>
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
            <Typography>Вид операции: {operation.operation_type.name}</Typography>
            <Typography>
              Время выполнения: {operation.operation_type.exec_time.substring(0, 2)}:
              {operation.operation_type.exec_time.substring(3, 5)}
            </Typography>

            <Typography>Информация об изделии</Typography>
            <Typography>Вид: {oper.product.product_type.name}</Typography>
            <Typography>Статус: {oper.product.product_status.name}</Typography>
            <Typography>Количество: {oper.product.amount}</Typography>
            <Typography>Формула для изделия</Typography>
            <ToothMarks teethList={oper.product.teeth.map(tooth => tooth.tooth_number)} />
          </Stack>
        </Box>
      </Modal>
    </div>
  );
}

export default ModalSetOperStatus;