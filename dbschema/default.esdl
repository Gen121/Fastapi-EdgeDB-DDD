module default {
    type OrderLine {
        orderid: str {
            constraint max_len_value(255);
            constraint exclusive
        };
        sku: str {constraint max_len_value(255)};
        required qty: int16;
        allocated_in: Batch;
    };

    type Batch {
        reference: str {
            constraint max_len_value(255);
            constraint exclusive
        };
        sku: str {constraint max_len_value(255)};
        eta: cal::local_date;
        required purchased_quantity: int16;
        multi link allocations := .<allocated_in[is OrderLine];
    };
}