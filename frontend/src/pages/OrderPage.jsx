import React, { useState, useEffect, useContext } from 'react';
import { useNavigate, useLocation } from "react-router-dom";
import InfoIcon from '@mui/icons-material/Info';
import {
  Typography,
  Grid, Stack, Box,
  TextField,
  Table, TableContainer, TableHead, TableBody, TableRow, TableCell,
  Button,
  Paper
} from '@mui/material';

import AuthContext from '../context/AuthContext';
import productService from '../servicies/ProductService';
import { isDirector, isLabAdmin, isChiefTech } from '../utils/Permissions';
import GridContainer from '../components/GridContainer';
import { boxContainerStyle } from './styles/OrderPageStyle';


const OrderPage = () => {
  const { authTokens, user } = useContext(AuthContext);
  const [order, setOrder] = useState({});
  const [products, setProducts] = useState([]);

  const { state } = useLocation();
  const navigate = useNavigate();

  const getOrderInfo = (orderId) => {
    productService.getForOrder(orderId)
      .then(res => {
        setProducts(res.data);
        setOrder(state.order);
      })
      .catch(err => {
        setProducts([]);
        setOrder({});
        console.log(err);
      });
  };

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }

    getOrderInfo(state.order.id);
  }, []);

  const renderProducts = () => {
    let i = 1;
    return products.map(product => (
      <TableRow key={product.id}>
        <TableCell>{i++}</TableCell>
        <TableCell>{product.productType.name}</TableCell>
        <TableCell>{product.productStatus.name}</TableCell>
        <TableCell>{product.amount}</TableCell>
        <TableCell>{product.productType.cost.toFixed(2)}</TableCell>
        <TableCell>{product.discount * 100}%</TableCell>
        <TableCell>{order.discount * 100}%</TableCell>
        <TableCell>{Math.max(product.discount, order.discount) * 100}%</TableCell>
        <TableCell>{product.cost.toFixed(2)}</TableCell>
        <TableCell>
          <Button variant="contained" onClick={() => navigate('/operations-for-product', { state: { product: product } })}>
            <InfoIcon />
          </Button>
        </TableCell>
      </TableRow>
    ));
  };

  return (
    <GridContainer>
      <Box sx={boxContainerStyle}>
        <Typography textAlign={"center"} variant="h4" component="h4" sx={{ marginBottom: 2 }}>
          Информация о заказе
        </Typography>
        <Box>
          <Stack spacing={2}>
            {
              products.length > 0 ?
                <TableContainer component={Paper}>
                  <Table label='Изделия'>
                    <TableHead>
                      <TableRow>
                        <TableCell>№</TableCell>
                        <TableCell>Тип изделия</TableCell>
                        <TableCell>Статус</TableCell>
                        <TableCell sx={{ width: "10%" }}>Кол-во</TableCell>
                        <TableCell>Цена</TableCell>
                        <TableCell>Скидка на изделие</TableCell>
                        <TableCell>Скидка на заказ</TableCell>
                        <TableCell>Рез. скидка</TableCell>
                        <TableCell>Сумма</TableCell>
                        <TableCell>Подробнее</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {renderProducts()}
                    </TableBody>
                  </Table>
                </TableContainer>
                : <p>Информации об изделиях нет</p>
            }
            <Grid sx={{
              display: "flex",
              direction: "row",
            }}>
              <TextField item
                sx={{ width: "100%", variant: "outlined" }}
                InputProps={{ readOnly: true }}
                InputLabelProps={{ shrink: true }}
                label="Заказчик"
                value={order?.user?.lastName + ' ' + order?.user?.firstName}
              />
              <TextField item
                sx={{ width: "100%", marginX: 2, variant: "outlined" }}
                InputProps={{ readOnly: true }}
                InputLabelProps={{ shrink: true }}
                label="Статус"
                value={order?.status?.name}
              />
              <TextField item
                sx={{ width: "100%", variant: "outlined" }}
                InputProps={{ readOnly: true }}
                InputLabelProps={{ shrink: true }}
                label="Дата"
                value={order?.orderDate}
              />
            </Grid>
            <Grid sx={{
              display: "flex",
              direction: "row",
            }}>
              {
                order?.discount !== 0 ?
                  <>
                    <TextField item
                      sx={{ width: "100%", variant: "outlined" }}
                      InputProps={{ readOnly: true }}
                      InputLabelProps={{ shrink: true }}
                      label="Сумма заказа (руб)"
                      value={order?.cost?.toFixed(2)}
                    />
                    <TextField item
                      sx={{ width: "100%", marginX: 2, variant: "outlined" }}
                      InputProps={{ readOnly: true }}
                      InputLabelProps={{ shrink: true }}
                      label="Скидка"
                      value={order?.discount * 100 + "%"}
                    />
                  </>
                  : <></>
              }
              <TextField item
                sx={{ width: "100%" }}
                InputProps={{ readOnly: true }}
                InputLabelProps={{ shrink: true }}
                label="Итоговая сумма заказа (руб)"
                variant="outlined"
                value={order?.cost?.toFixed(2)}
              />
            </Grid>
            {
              order?.status?.number === 1 && isLabAdmin(user) &&
              <Button variant="contained" sx={{ paddingY: 1 }}
                onClick={() => navigate('/process-order', { state: { order: order, products: products } })}>
                Начать формирование наряда
              </Button>
            }
            {
              order?.status?.number === 2 && (isLabAdmin(user) || isChiefTech(user) || isDirector(user)) &&
              <Button variant="contained" sx={{ paddingY: 1 }}
                onClick={() => navigate('/assign-operations', { state: { order: order, products: products } })}>
                Назначить операции
              </Button>
            }
          </Stack>
        </Box>
      </Box>
    </GridContainer>
  );
};

export default OrderPage;
