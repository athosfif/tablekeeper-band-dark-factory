# Stage 2 independent acceptance design

Recorded2026-09-26 before inspecting Stage2 implementation or official Stage2 test source. Derived from the complete inherited/current specifications in the dispatch. Reviewer owns evidence only. The existing Stage1 source/evidence is read-only. Source review begins only after this design and supplementary cases are authored.

Baseline: delivery e5c256641653de82a97222d1126308fbde6188f6; tested source0f96bf0cd889959d134ca6f8a5ee3066bbe459f8; Stage1 tree0050accbdc6d0457ffdc73de6365158e65c1808b. Upstream803560d2a678ace1414465c098eb0ab5380ffade. Read the active stages2–4 plan; obligations below independently exercise its C/U/T rows.

## Inherited guarantees and deployment

Copy the28 reviewer HTTP groups into new evidence; preserve the original copy. Adjust an assertion only when a later specification explicitly changes a response shape (new table_ids/config field), recording the reason. Retain authentication/privacy, every error/precedence, full parsed-body/idempotency/deep JSON,50-request atomicity, arbitrary dates, grids/DST and independent snapshot cases. Old imported receipts are exact original JSON, not upgraded shapes. Verify clean committed handoff and earlier tree before/after all runs. Build only stage2, use default8080 and alternate PORT,2CPU/2GiB, fresh containers/no volumes/internal network, ordinary5s/control10s, healthy60s. Inspect screenshots and offline assets. Run cumulative official isolated Stage1+2 and actual Stage3 overshoot; preserve counts/errors and never equate skips/setup failures with pass.

## API cases

1. Fixture with4 tables in deliberately nonlexical order, capacities2/3/4/5 and pairs declared in reversed/nonlexical order. For party sizes1..10 compute exact singles then pairs options and exact member order independently. Full slots remain; single IDs never include pair capacity. Nontransitive undeclared pair fails even if graph-connected.
2. Both table_id/table_ids422; empty,duplicate,wrong-type/unknown IDs; >2 and undeclared pair combination_not_allowed; oversized party party_exceeds_capacity. Verify state/keys unchanged on rejection and retry after repair of request. Reverse valid pair normalizes declared order; receipt equality still compares request JSON order.
3. Pair create occupies both; either single or intersecting pair conflicts. A disjoint single succeeds. Half-open endpoints permit adjacency. Cancellation frees both immediately. Cancelled pair seed occupies neither, remains listed/lookup; default seedstatusconfirmed.
4. PATCH transitions single→pair→single, shape table_id present iff1 member; atomic failure preserves all values/occupancy. Unknown fields/no-op/reversed-pair no-op. Batch swap/cycle among disjoint pairs, retained listed occupancy and member collision; input ordering, original receipts and key rollback.
5.50 contenders mixing pair and member single at same time: one winning compatible set, no overlapping member assignments.50 identical pair retries: exactly1x201+49x200identicalreceipt.50 pair/move conflicts obey serial execution semantics; reads never see partial assignments.
6. Export/import same-stage pairs and cancelledseeds, then actual populated acceptedStage1→Stage2 upgrade. Preserve multiple sessions/hashlogin,identities/timestamps,old original create/batchreceipts afterchanged/cancelledstate,failedkeys,destinationcredential removal; corrupt importrollback. Source changes after export cannot alter imported snapshot. No serialized exports/tokens saved.

## Browser cases and evidence

Use only public test IDs/visible labels. Real server requests remain authoritative. Capture screenshots of desktop and375px flows with synthetic identities. Do not save localStorage or network response bodies containing tokens.

1. Direct HTML routes/,/signup,/login,/lookup; navigation consistent. Signup/loginerrors onlywhenpresent,displayname current-user everyroute,logout removes session UI. Signedout availablecell requireslogin/error; unavailablecell inert.
2. Search grid independently compare each table/time data-available to API. Everytableperslot represented; labels restaurant/tableshumanreadable. Closedweekday replacesgridwithno-slots. Pair cells ordered as declared, containbothlabels. Booking summary time/alllabels,party prefilled.
3. Successful single/pair booking keepsform,exactreference and restaurant/time/tablelabels; confirmation-tables allmembers; repeatedunchangedsubmit usesidenticalkey/body andsameoriginalreference; changedpartynewkey andconfirmedrejectionifoccupied. No fabricatedcachedsuccess.
4. Openform then competingclientoccupiesselection:409 booking-error,availability refresh,data-availablefalse,retainform/inputs,no newconfirmation. Repeat withpairmemberlost.
5. Intercept POST: let servercommit via route.fetch,thenabortdelivery. UI showsnonemptybooking-uncertain,neitherbooking-error nornewconfirmation; unchangedretrysamebody/key;originalreference,recoveredonce andclearsuncertainty. Alsoabortbeforecommit,thenretrynewfirstsuccess;testsingle+pair. Confirmserverreservationcount.
6. Delay searchA's restaurantdetails/availability while Bchangesrestaurant/date/party;deliverBfirst thenA. Grid/labels/formmustremainB. IncludeBemptyday topreventoldgridresurrection and lateerrorfromA.
7. Lookup ownreference,status exactconfirmed/cancelled,alltablelabels;cancelremovesbutton,freesmembers;unknown/otherownererror;cutoffrefusal remainsconfirmed. Checkeachscreen signed-inheader.
8. Upgrade in openpage: route API through dynamic backend to acceptedStage1 initially while UI assets are Stage2. Signin,submitbookinglostaftercommit,exportoldservice andimportfreshStage2,retargetAPI betweenrequests,unchangedpage/formretryrecoversoriginalStage1receipt. Retainedsession/referenceworks lookup withoutrelogin/reload. Separatelypairsameserviceexport/importretainsuncertainretry.
9. Desktop/375 screenshots: empty/loading/grid/selected/confirmed/refused/uncertain. Assertdocument scrollWidth<=innerWidth,visiblelabels,keyboardfocus andtouchgeometry. Manual rendered assessment ofcontrast,type,hierarchy,calmoffwhite/greenpalette and clearstates. Offline browserblocksnonlocalrequests;noscripts/fonts/assetsneedexternalnetwork.

## Verdict evidence

Newdirectoryperrun; fullcommit/treechecks,sourcehashes,commands,exitstatuses,group/count/timinglogs,screenshots. Genuineexpected/actualdefects go toBuilder withcompleteapplicablecontract; Buildermakesnewcommits. Acceptance requirescompletecumulativeisolatedandsupplementary/API/browser/migrationcoverage. No laterstagecode beforeexplicitacceptance. This design is a coverage obligation, not an assertion that tests already passed.
