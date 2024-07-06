import React, { useState, useEffect, useContext } from 'react';
import { useNavigate, useLocation } from "react-router-dom";
import InfoIcon from '@mui/icons-material/Info';
import {
  Typography,
  Grid, Stack,
  TextField,
  Table, TableContainer, TableHead, TableBody, TableRow, TableCell,
  Button,
  Paper
} from '@mui/material';

import AuthContext from '../context/AuthContext';
import productService from '../servicies/ProductService';
import orderService from '../servicies/OrderService';
import { isLabAdmin } from '../utils/Permissions';


const blockStyle = {
  paddingY: 2,
  paddingX: 2
};

const OrderProcessingPage = () => {
  const { authTokens, user } = useContext(AuthContext);
  const [order, setOrder] = useState({});
  const [products, setProducts] = useState([]);
  const [curProdIdx, setCurProdIdx] = useState(0);

  const { state } = useLocation();
  const navigate = useNavigate();

  const getProductsWithOperations = () => {
    productService.getWithOperationsForOrder(state.order.id)
      .then(res => {
        for (let i = 0; i < res.data.length; i++) {
          res.data[i].number = i;
        }
        setProducts(res.data);
      })
      .catch(err => {
        setProducts([]);
        console.log(err);
      });
  };

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }

    if (!isLabAdmin(user)) {
      navigate('/');
    }

    setOrder(state.order);

    getProductsWithOperations();
  }, []);

  const handleOrderDiscountChanged = (e) => {
    const discount = e.target.value;
    if (discount >= 0 && discount < 100) {
      setOrder({ ...order, discount: e.target.value });
    }
  };

  const handleProductDiscountChanged = (e) => {
    const discount = e.target.value;
    if (discount >= 0 && discount < 100) {
      products[curProdIdx].discount = discount;
      setProducts([...products]);
    }
  };

  const getProductCost = (product) => {
    const discount = Math.max(product.discount, order.discount);
    return product.productType.cost * product.amount * (1 - discount / 100);
  };

  const getOrderCost = () => {
    return products.reduce((partialSum, product) => partialSum + getProductCost(product), 0);
  };

  const renderProducts = () => {
    return products.map(product => (
      <TableRow key={product.id}>
        <TableCell>{product.productType.name}</TableCell>
        <TableCell>{getProductCost(product).toFixed(2)}</TableCell>
        <TableCell>
          <Button variant="contained" onClick={() => setCurProdIdx(product.number)}>
            <InfoIcon />
          </Button>
        </TableCell>
      </TableRow>
    ));
  };

  const renderOperations = () => {
    return products[curProdIdx].operations.map(operation => (
      <TableRow key={operation.id}>
        <TableCell>{operation.operationType.name}</TableCell>
        <TableCell>{operation.operationType.execTime}</TableCell>
      </TableRow>
    ));
  };

  const submitOrder = () => {
    orderService.confirmOrder(order, products)
      .then(res => {
        navigate("/order", { state: { order: res.data } });
      })
      .catch(err => {
        console.log(err);
      });
  };

  return (
    <Grid container justifyContent='center' spacing={2} marginTop={1}>
      <Grid item xs={5}>
        <Stack spacing={2}>
          <Stack container component={Paper} sx={blockStyle} spacing={1}>
            <Typography textAlign='center'>
              <b>Информация о заказе</b>
            </Typography><hr />
            <Typography>
              Заказчик: {order?.user?.lastName + ' ' + order?.user?.firstName}
            </Typography>
            <Typography>
              Дата оформления: {order?.orderDate}
            </Typography>
            <Typography>
              Сумма заказа: {getOrderCost().toFixed(2)} руб.
            </Typography>
            <Stack direction='row' alignItems='center'>
              <Typography>
                Скидка (%):
              </Typography>
              <TextField
                sx={{ marginX: 2 }}
                type='number'
                inputProps={{ step: 0.01, min: 0, max: 99.99, style: { height: '8px' } }}
                onChange={handleOrderDiscountChanged}
                value={order?.discount}
              />
            </Stack>
            <Typography>
              Итоговая сумма заказа: {(order?.cost * (1 - order?.discount / 100)).toFixed(2)} руб.
            </Typography>
            <Button variant='contained' onClick={submitOrder}>
              Оформить наряд
            </Button>
            <hr />
            <Typography textAlign='center'>
              <b>Список изделий</b>
            </Typography>
            <hr />
            {
              products.length > 0 ?
                <TableContainer component={Paper}>
                  <Table label='Изделия'>
                    <TableHead>
                      <TableRow>
                        <TableCell>Тип изделия</TableCell>
                        <TableCell>Итоговая сумма (руб)</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {renderProducts()}
                    </TableBody>
                  </Table>
                </TableContainer>
                : <p>Информации об изделиях нет</p>
            }
          </Stack>
        </Stack>
      </Grid>
      <Grid item xs={5}>
        <Stack spacing={2}>
          <Stack component={Paper} sx={blockStyle} spacing={1}>
            <Typography textAlign='center'>
              <b>Информация об изделии</b>
            </Typography><hr />
            {
              products.length > 0 ?
                <>
                  <Typography>
                    Тип изделия: {products[curProdIdx].productType.name}
                  </Typography>
                  <Typography>
                    Стоимость 1-го изделия: {products[curProdIdx].productType.cost.toFixed(2)} руб.
                  </Typography>
                  <Typography>
                    Количество: {products[curProdIdx].amount}
                  </Typography>
                  <Typography>
                    Сумма: {(products[curProdIdx].productType.cost * products[curProdIdx].amount).toFixed(2)} руб.
                  </Typography>
                  <Stack direction='row' alignItems='center'>
                    <Typography>
                      Скидка на изделие (%):
                    </Typography>
                    <TextField
                      sx={{ marginX: 2 }}
                      type='number'
                      inputProps={{ step: 0.01, min: 0, max: 99.99, style: { height: '8px' } }}
                      onChange={handleProductDiscountChanged}
                      value={products[curProdIdx].discount}
                    />
                  </Stack>
                  <Typography>
                    Результирующая скидка (%): {Math.max(products[curProdIdx].discount, order.discount)}
                  </Typography>
                  <Typography>
                    Итоговая сумма: {getProductCost(products[curProdIdx]).toFixed(2)} руб.
                  </Typography>
                </>
                : <Typography textAlign='center'>Нет изделий в заказе</Typography>
            }
            <hr />
            <Typography textAlign='center'>
              <b>Список операций</b>
            </Typography>
            <hr />
            {
              (products.length > 0) && (products[curProdIdx]?.operations.length > 0) ?
                <TableContainer component={Paper}>
                  <Table label='Изделия'>
                    <TableHead>
                      <TableRow>
                        <TableCell>Тип операции</TableCell>
                        <TableCell>Время выполнения</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {renderOperations()}
                    </TableBody>
                  </Table>
                </TableContainer>
                : <Typography textAlign='center'>Информации об операциях нет</Typography>
            }
          </Stack>
        </Stack>
      </Grid>
    </Grid>
  );
};

export default OrderProcessingPage;
