CREATE MIGRATION m1rdd25gj4fgovsmvci523rnw75qrpgxa5qwvbimpyzaeevthsdzcq
    ONTO initial
{
  CREATE FUTURE nonrecursive_access_policies;
  CREATE TYPE default::Batch {
      CREATE PROPERTY eta: cal::local_date;
      CREATE REQUIRED PROPERTY purchased_quantity: std::int16;
      CREATE PROPERTY reference: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  CREATE TYPE default::OrderLine {
      CREATE PROPERTY orderid: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE REQUIRED PROPERTY qty: std::int16;
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  ALTER TYPE default::Batch {
      CREATE MULTI LINK allocations: default::OrderLine {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  ALTER TYPE default::OrderLine {
      CREATE LINK allocted_in := (.<allocations[IS default::Batch]);
  };
};
