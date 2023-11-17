import os
import pandas as pd

from syscore.exceptions import missingData
from syscore.pandas.pdutils import check_df_equals, check_ts_equals
from syscore.dateutils import CALENDAR_DAYS_IN_YEAR
from syscore.dateutils import DAILY_PRICE_FREQ, HOURLY_FREQ

from sysdata.data_blob import dataBlob

from sysdata.parquet.parquet_adjusted_prices import parquetFuturesAdjustedPricesData
from sysdata.parquet.parquet_capital import parquetCapitalData
from sysdata.parquet.parquet_futures_per_contract_prices import parquetFuturesContractPriceData

from sysdata.csv.csv_futures_contracts import csvFuturesContractData
from sysdata.csv.csv_multiple_prices import csvFuturesMultiplePricesData
from sysdata.csv.csv_spot_fx import csvFxPricesData
from sysdata.csv.csv_contract_position_data import csvContractPositionData
from sysdata.csv.csv_strategy_position_data import csvStrategyPositionData
from sysdata.csv.csv_historic_orders import (
    csvStrategyHistoricOrdersData,
    csvContractHistoricOrdersData,
    csvBrokerHistoricOrdersData,
)
from sysdata.csv.csv_optimal_position import csvOptimalPositionData
from sysdata.csv.csv_spread_costs import csvSpreadCostData
from sysdata.csv.csv_roll_state_storage import csvRollStateData
from sysdata.csv.csv_spreads import csvSpreadsForInstrumentData

from sysdata.arctic.arctic_futures_per_contract_prices import (
    arcticFuturesContractPriceData,
)
from sysdata.arctic.arctic_multiple_prices import arcticFuturesMultiplePricesData
from sysdata.arctic.arctic_adjusted_prices import arcticFuturesAdjustedPricesData
from sysdata.arctic.arctic_spotfx_prices import arcticFxPricesData
from sysdata.arctic.arctic_spreads import arcticSpreadsForInstrumentData
from sysdata.arctic.arctic_capital import arcticCapitalData
from sysdata.arctic.arctic_historic_strategy_positions import arcticStrategyPositionData
from sysdata.arctic.arctic_historic_contract_positions import arcticContractPositionData
from sysdata.arctic.arctic_optimal_positions import arcticOptimalPositionData

from sysdata.mongodb.mongo_futures_contracts import mongoFuturesContractData
from sysdata.mongodb.mongo_historic_orders import (
    mongoBrokerHistoricOrdersData,
    mongoContractHistoricOrdersData,
    mongoStrategyHistoricOrdersData,
)
from sysdata.mongodb.mongo_spread_costs import mongoSpreadCostData
from sysdata.mongodb.mongo_roll_state_storage import mongoRollStateData

from sysobjects.contracts import futuresContract
from sysobjects.production.tradeable_object import instrumentStrategy

from sysproduction.data.directories import get_csv_backup_directory, get_csv_dump_dir
from sysproduction.data.strategies import get_list_of_strategies


def backup_arctic_to_parquet():

        backup_data = get_data_blob("backup_arctic_to_parquet")
        log = backup_data.log

        log.debug("Dumping from arctic, mongo to parquet files")
        backup_futures_contract_prices_to_parquet(backup_data)
        #backup_spreads_to_csv(backup_data)
        #backup_fx_to_csv(backup_data)
        #backup_multiple_to_csv(backup_data)
        backup_adj_to_parquet(backup_data)
        #backup_strategy_position_data(backup_data)
        #backup_contract_position_data(backup_data)
        #backup_historical_orders(backup_data)
        backup_capital(backup_data)
        #backup_contract_data(backup_data)
        #backup_spread_cost_data(backup_data)
        #backup_optimal_positions(backup_data)
        #backup_roll_state_data(backup_data)


def get_data_blob(logname):

    data = dataBlob(
         keep_original_prefix=True, log_name=logname
    )

    data.add_class_list(
        [
            #csvBrokerHistoricOrdersData,
            parquetCapitalData,
            #csvContractHistoricOrdersData,
            #csvContractPositionData,
            parquetFuturesAdjustedPricesData,
            #csvFuturesContractData,
            parquetFuturesContractPriceData,
            #csvFuturesMultiplePricesData,
            #csvFxPricesData,
            #csvOptimalPositionData,
            #csvRollStateData,
            #csvSpreadCostData,
            #csvSpreadsForInstrumentData,
            #csvStrategyHistoricOrdersData,
            #csvStrategyPositionData,
        ]
    )

    data.add_class_list(
        [
            arcticCapitalData,
            arcticFuturesAdjustedPricesData,
            arcticFuturesContractPriceData,
            arcticFuturesMultiplePricesData,
            arcticFxPricesData,
            arcticSpreadsForInstrumentData,
            mongoBrokerHistoricOrdersData,
            mongoContractHistoricOrdersData,
            arcticContractPositionData,
            mongoFuturesContractData,
            arcticOptimalPositionData,
            mongoRollStateData,
            mongoSpreadCostData,
            mongoStrategyHistoricOrdersData,
            arcticStrategyPositionData,
        ]
    )

    return data


# Write function for each thing we want to backup
# Think about how to check for duplicates (data frame equals?)
def backup_adj_to_parquet(data):
    instrument_list = data.arctic_futures_adjusted_prices.get_list_of_instruments()
    for instrument_code in instrument_list:
        backup_adj_to_parquet_for_instrument(data, instrument_code)

def backup_adj_to_parquet_for_instrument(data: dataBlob, instrument_code: str):
    arctic_data = data.arctic_futures_adjusted_prices.get_adjusted_prices(
        instrument_code
    )
    try:
        data.parquet_futures_adjusted_prices.add_adjusted_prices(
            instrument_code, arctic_data, ignore_duplication=True
        )
        px = data.parquet_futures_adjusted_prices.get_adjusted_prices(
        instrument_code
            )
        data.log.debug(
            "Written .parquet backup for adjusted prices %s, %s" % (instrument_code,str(px))
        )
    except BaseException:
        data.log.warning(
            "Problem writing .parquet backup for adjusted prices %s" % instrument_code
        )


# Futures contract data
def backup_futures_contract_prices_to_parquet(data):
    instrument_list = (
        data.arctic_futures_contract_price.get_list_of_instrument_codes_with_merged_price_data()
    )
    for instrument_code in instrument_list:
        backup_futures_contract_prices_for_instrument_to_parquet(
            data=data,
            instrument_code=instrument_code
        )


def backup_futures_contract_prices_for_instrument_to_parquet(
    data: dataBlob, instrument_code: str
):
    list_of_contracts = data.arctic_futures_contract_price.contracts_with_merged_price_data_for_instrument_code(
        instrument_code
    )

    for futures_contract in list_of_contracts:
        backup_futures_contract_prices_for_contract_to_parquet(
            data=data,
            futures_contract=futures_contract,
        )


def backup_futures_contract_prices_for_contract_to_parquet(
    data: dataBlob, futures_contract: futuresContract
):

    arctic_data = (
        data.arctic_futures_contract_price.get_merged_prices_for_contract_object(
            futures_contract
        )
    )

    data.parquet_futures_contract_price.write_merged_prices_for_contract_object(
        futures_contract,
        arctic_data,
        ignore_duplication=True,
    )
    parquet_data = (
        data.parquet_futures_contract_price.get_merged_prices_for_contract_object(
            futures_contract
        )
    )
    data.log.debug(
        "Written backup .csv of prices for %s was %s now %s" % (str(futures_contract), arctic_data, parquet_data)
    )

    for frequency in [DAILY_PRICE_FREQ, HOURLY_FREQ]:
        arctic_data = (
            data.arctic_futures_contract_price.get_prices_at_frequency_for_contract_object(
                futures_contract,
                frequency=frequency
            )
        )

        data.parquet_futures_contract_price.write_prices_at_frequency_for_contract_object(
            futures_contract_object=futures_contract,
            futures_price_data=arctic_data,
            frequency=frequency,
            ignore_duplication=True
        )
        parquet_data = (
            data.parquet_futures_contract_price.get_prices_at_frequency_for_contract_object(
                futures_contract,
                frequency=frequency
            )
        )
        data.log.debug(
            "Written backup .csv of prices at frequency %s for %s was %s now %s" % (str(frequency), str(futures_contract), arctic_data, parquet_data)
        )


# fx
def backup_fx_to_csv(data):
    fx_codes = data.arctic_fx_prices.get_list_of_fxcodes()
    for fx_code in fx_codes:
        arctic_data = data.arctic_fx_prices.get_fx_prices(fx_code)
        csv_data = data.csv_fx_prices.get_fx_prices(fx_code)
        if check_ts_equals(arctic_data, csv_data):
            data.log.debug("No fx backup needed for %s" % fx_code)
        else:
            # Write backup
            try:
                data.csv_fx_prices.add_fx_prices(
                    fx_code, arctic_data, ignore_duplication=True
                )
                data.log.debug("Written .csv backup for %s" % fx_code)
            except BaseException:
                data.log.warning("Problem writing .csv backup for %s" % fx_code)


def backup_multiple_to_csv(data):
    instrument_list = data.arctic_futures_multiple_prices.get_list_of_instruments()
    for instrument_code in instrument_list:
        backup_multiple_to_csv_for_instrument(data, instrument_code)


def backup_multiple_to_csv_for_instrument(data, instrument_code: str):
    arctic_data = data.arctic_futures_multiple_prices.get_multiple_prices(
        instrument_code
    )
    csv_data = data.csv_futures_multiple_prices.get_multiple_prices(instrument_code)

    if check_df_equals(arctic_data, csv_data):
        data.log.debug("No multiple prices backup needed for %s" % instrument_code)
        pass
    else:
        try:
            data.csv_futures_multiple_prices.add_multiple_prices(
                instrument_code, arctic_data, ignore_duplication=True
            )
            data.log.debug(
                "Written .csv backup multiple prices for %s" % instrument_code
            )
        except BaseException:
            data.log.warning(
                "Problem writing .csv backup multiple prices for %s" % instrument_code
            )






def backup_spreads_to_csv(data: dataBlob):
    instrument_list = data.arctic_spreads_for_instrument.get_list_of_instruments()
    for instrument_code in instrument_list:
        backup_spreads_to_csv_for_instrument(data, instrument_code)


def backup_spreads_to_csv_for_instrument(data: dataBlob, instrument_code: str):
    arctic_data = data.arctic_spreads_for_instrument.get_spreads(instrument_code)
    csv_data = data.csv_spreads_for_instrument.get_spreads(instrument_code)

    if check_ts_equals(arctic_data, csv_data):
        data.log.debug("No spreads backup needed for %s" % instrument_code)
        pass
    else:
        try:
            data.csv_spreads_for_instrument.add_spreads(
                instrument_code, arctic_data, ignore_duplication=True
            )
            data.log.debug("Written .csv backup for spreads %s" % instrument_code)
        except BaseException:
            data.log.warning(
                "Problem writing .csv backup for spreads %s" % instrument_code
            )


def backup_contract_position_data(data):
    instrument_list = (
        data.arctic_contract_position.get_list_of_instruments_with_any_position()
    )
    for instrument_code in instrument_list:
        contract_list = (
            data.arctic_contract_position.get_list_of_contracts_for_instrument_code(
                instrument_code
            )
        )
        for contract in contract_list:
            try:
                arctic_data = data.arctic_contract_position.get_position_as_series_for_contract_object(
                    contract
                )
            except missingData:
                print("No data to write to .csv")
            else:
                data.csv_contract_position.overwrite_position_series_for_contract_object_without_checking(
                    contract, arctic_data
                )
            data.log.debug(
                "Backed up %s %s contract position data" % (instrument_code, contract)
            )


def backup_strategy_position_data(data):
    strategy_list = get_list_of_strategies(data)
    instrument_list = (
        data.arctic_contract_position.get_list_of_instruments_with_any_position()
    )
    for strategy_name in strategy_list:
        for instrument_code in instrument_list:
            instrument_strategy = instrumentStrategy(
                strategy_name=strategy_name, instrument_code=instrument_code
            )
            try:
                arctic_data = data.arctic_strategy_position.get_position_as_series_for_instrument_strategy_object(
                    instrument_strategy
                )
            except missingData:
                continue
            data.csv_strategy_position.overwrite_position_series_for_instrument_strategy_without_checking(
                instrument_strategy, arctic_data
            )
            data.log.debug(
                "Backed up %s %s strategy position data"
                % (instrument_code, strategy_name)
            )


def backup_historical_orders(data):
    data.log.debug("Backing up strategy orders...")
    list_of_orders = [
        data.mongo_strategy_historic_orders.get_order_with_orderid(id)
        for id in data.mongo_strategy_historic_orders.get_list_of_order_ids()
    ]
    data.csv_strategy_historic_orders.write_orders(list_of_orders)
    data.log.debug("Done")

    data.log.debug("Backing up contract orders...")
    list_of_orders = [
        data.mongo_contract_historic_orders.get_order_with_orderid(order_id)
        for order_id in data.mongo_contract_historic_orders.get_list_of_order_ids()
    ]
    data.csv_contract_historic_orders.write_orders(list_of_orders)
    data.log.debug("Done")

    data.log.debug("Backing up broker orders...")
    list_of_orders = [
        data.mongo_broker_historic_orders.get_order_with_orderid(order_id)
        for order_id in data.mongo_broker_historic_orders.get_list_of_order_ids()
    ]
    data.csv_broker_historic_orders.write_orders(list_of_orders)
    data.log.debug("Done")


def backup_capital(data):
    strategy_list = data.arctic_capital._get_list_of_strategies_with_capital_including_total()
    for strategy_name in strategy_list:
        strategy_capital_data=data.arctic_capital.get_capital_pd_df_for_strategy(strategy_name)
        data.parquet_capital.update_capital_pd_df_for_strategy(strategy_name=strategy_name, updated_capital_df=strategy_capital_data)
        written_data = data.parquet_capital.get_capital_pd_df_for_strategy(strategy_name)
        print("Wrote capital data for strategy %s, was %s now %s" % (strategy_name, str(strategy_capital_data), str(written_data)))

    return strategy_capital_data


def add_total_capital_to_strategy_capital_dict_return_df(
    data: dataBlob, capital_data: dict
) -> pd.DataFrame:

    strategy_capital_as_df = pd.concat(capital_data, axis=1)
    total_capital = data.arctic_capital.get_df_of_all_global_capital()
    capital_data = pd.concat([strategy_capital_as_df, total_capital], axis=1)

    capital_data = capital_data.ffill()

    return capital_data


def backup_optimal_positions(data):

    strategy_instrument_list = (
        data.arctic_optimal_position.get_list_of_instrument_strategies_with_optimal_position()
    )

    for instrument_strategy in strategy_instrument_list:
        try:
            arctic_data = data.arctic_optimal_position.get_optimal_position_as_df_for_instrument_strategy(
                instrument_strategy
            )
        except missingData:
            continue
        data.csv_optimal_position.write_optimal_position_as_df_for_instrument_strategy_without_checking(
            instrument_strategy, arctic_data
        )
        data.log.debug("Backed up %s  optimal position data" % str(instrument_strategy))


def backup_spread_cost_data(data):
    spread_cost_as_series = data.mongo_spread_cost.get_spread_costs_as_series()
    data.csv_spread_cost.write_all_instrument_spreads(spread_cost_as_series)
    data.log.debug("Backed up spread cost data")


def backup_roll_state_data(data):
    instrument_list = data.mongo_roll_state.get_list_of_instruments()
    roll_state_list = []
    for instrument_code in instrument_list:
        roll_state = data.mongo_roll_state.get_name_of_roll_state(instrument_code)
        roll_state_list.append(roll_state)

    roll_state_df = pd.DataFrame(roll_state_list, index=instrument_list)
    roll_state_df.columns = ["state"]
    data.csv_roll_state.write_all_instrument_data(roll_state_df)
    data.log.debug("Backed up roll state")


def backup_contract_data(data):
    instrument_list = (
        data.mongo_futures_contract.get_list_of_all_instruments_with_contracts()
    )
    for instrument_code in instrument_list:
        contract_list = (
            data.mongo_futures_contract.get_all_contract_objects_for_instrument_code(
                instrument_code
            )
        )
        data.csv_futures_contract.write_contract_list_as_df(
            instrument_code, contract_list
        )
        data.log.debug("Backed up contract data for %s" % instrument_code)


def backup_csv_dump(data):
    source_path = get_csv_dump_dir()
    destination_path = get_csv_backup_directory()
    data.log.debug("Copy from %s to %s" % (source_path, destination_path))
    os.system("rsync -av %s %s" % (source_path, destination_path))


if __name__ == "__main__":
    backup_arctic_to_parquet()
