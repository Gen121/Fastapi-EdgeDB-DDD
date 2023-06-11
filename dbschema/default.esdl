module default {
    type Batch {
        required purchased_quantity: int16;
        eta: datetime;
        reference: str {constraint max_len_value(255)};
        sku: str {constraint max_len_value(255)};
        multi allocations: OrderLine {constraint exclusive};
    };

    type OrderLine {
        orderid: str {constraint max_len_value(255)};
        required qty: int16;
        sku: str {constraint max_len_value(255)};
        link allocted_in := .<allocations[is Batch];
    }
}