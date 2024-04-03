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

const OrderPage = () => {
  const { authTokens } = useContext(AuthContext);
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
  }

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
        <TableCell>{product.product_type.name}</TableCell>
        <TableCell>{product.product_status.name}</TableCell>
        <TableCell>{product.amount}</TableCell>
        <TableCell>{product.product_type.cost.toFixed(2)}</TableCell>
        <TableCell>{product.discount * 100}%</TableCell>
        <TableCell>{product.cost.toFixed(2)}</TableCell>
        <TableCell>
          <Button variant="contained" onClick={() => navigate('/operations-for-product', { state: { product: product } })}>
            <InfoIcon />
          </Button>
        </TableCell>
      </TableRow>
    ));
  }

  return (
    <Grid container sx={{
      spacing: 0,
      alignItems: "center",
      justifyContent: "center"
    }}>
      <Box sx={{
        border: 1,
        borderRadius: 2,
        borderColor: "#4d4c4c",
        padding: 3,
        marginTop: 5,
        width: "60%"
      }}>
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
                        <TableCell>Скидка</TableCell>
                        <TableCell>Сумма</TableCell>
                        <TableCell>Подробнее</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {renderProducts()}
                    </TableBody>
                  </Table>
                </TableContainer>
                : <p for="products">Изделия для заказа</p>
            }
            <TextField
              InputProps={{ readOnly: true }}
              InputLabelProps={{ shrink: true }}
              label="Заказчик"
              variant="outlined"
              value={order?.user?.last_name + ' ' + order?.user?.first_name}
            />
            <TextField
              InputProps={{ readOnly: true }}
              InputLabelProps={{ shrink: true }}
              label="Статус"
              variant="outlined"
              value={order?.status?.name}
            />
            <TextField
              InputProps={{ readOnly: true }}
              InputLabelProps={{ shrink: true }}
              label="Дата"
              variant="outlined"
              value={order?.order_date}
            />
            <Grid sx={{
              display: "flex",
              direction: "row",
            }}>
              {
                order?.discount !== 0 ?
                  <>
                    <TextField item
                      sx={{ width: "100%" }}
                      InputProps={{ readOnly: true }}
                      InputLabelProps={{ shrink: true }}
                      label="Сумма заказа (руб)"
                      variant="outlined"
                      value={order?.cost?.toFixed(2)}
                    />
                    <TextField item
                      sx={{ width: "100%", marginX: 2 }}
                      InputProps={{ readOnly: true }}
                      InputLabelProps={{ shrink: true }}
                      label="Скидка"
                      variant="outlined"
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
                value={(order?.cost * (1 - order?.discount)).toFixed(2)}
              />
            </Grid>
          </Stack>
        </Box>
      </Box>
    </Grid>
  )
}

export default OrderPage;
