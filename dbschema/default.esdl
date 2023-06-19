module default {
    type Batch {
        reference: str {constraint max_len_value(255)};
        sku: str {constraint max_len_value(255)};
        eta: cal::local_date;
        required purchased_quantity: int16;
        multi allocations: OrderLine {constraint exclusive};
    };

    type OrderLine {
        orderid: str {constraint max_len_value(255)};
        sku: str {constraint max_len_value(255)};
        required qty: int16;
        link allocted_in := .<allocations[is Batch];
    }
}