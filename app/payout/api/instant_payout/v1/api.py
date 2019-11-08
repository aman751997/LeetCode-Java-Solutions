from datetime import datetime

from starlette.status import HTTP_200_OK
from fastapi import APIRouter, Body, Path, Depends, Query

from app.commons.api.errors import BadRequestErrorCode, payment_error_message_maps
from app.commons.api.models import BadRequestError
from app.payout.api.instant_payout.v1 import models
from app.payout.core.instant_payout.models import (
    EligibilityCheckRequest,
    CreateAndSubmitInstantPayoutRequest,
)
from app.payout.core.instant_payout.processor import InstantPayoutProcessors
from app.payout.models import PayoutAccountId
from app.payout.service import create_instant_payout_processors

api_tags = ["InstantPayoutsV1"]
router = APIRouter()


@router.post(
    "/",
    status_code=HTTP_200_OK,
    operation_id="SubmitInstantPayout",
    response_model=models.InstantPayout,
    tags=api_tags,
)
async def submit_instant_payout(
    body: models.InstantPayoutCreate = Body(...),
    instant_payout_processors: InstantPayoutProcessors = Depends(
        create_instant_payout_processors
    ),
):
    internal_request = CreateAndSubmitInstantPayoutRequest(
        payout_account_id=body.payout_account_id,
        amount=body.amount,
        currency=body.currency,
        card=body.card,
    )
    internal_instant_payout_response = await instant_payout_processors.create_and_submit_instant_payout(
        request=internal_request
    )
    return models.InstantPayout(**internal_instant_payout_response.dict())


@router.get(
    "/{payout_account_id}/eligibility",
    status_code=HTTP_200_OK,
    operation_id="CheckInstantPayoutEligibility",
    response_model=models.PaymentEligibility,
    tags=api_tags,
)
async def check_instant_payout_eligibility(
    payout_account_id: PayoutAccountId = Path(..., description="Payout Account ID"),
    local_start_of_day: int = Query(
        default=...,
        description="Instant Payout entity's local start of today in timestamp",
    ),
    instant_payout_processors: InstantPayoutProcessors = Depends(
        create_instant_payout_processors
    ),
):
    # raise invalid request error if converting local_start_of_day overflows
    # todo: Leon, replace with processor layer error when refactoring errors.
    try:
        created_after = datetime.fromtimestamp(local_start_of_day / 1.0)
    except OverflowError as e:
        raise BadRequestError(
            error_code=BadRequestErrorCode.INVALID_VALUE_ERROR,
            err_message=payment_error_message_maps[
                BadRequestErrorCode.INVALID_VALUE_ERROR
            ],
        ) from e

    internal_request = EligibilityCheckRequest(
        payout_account_id=payout_account_id, created_afer=created_after
    )
    internal_response = await instant_payout_processors.check_instant_payout_eligibility(
        internal_request
    )
    return models.PaymentEligibility(**internal_response.dict())
