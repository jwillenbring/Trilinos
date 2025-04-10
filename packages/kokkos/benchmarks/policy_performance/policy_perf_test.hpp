//@HEADER
// ************************************************************************
//
//                        Kokkos v. 4.0
//       Copyright (2022) National Technology & Engineering
//               Solutions of Sandia, LLC (NTESS).
//
// Under the terms of Contract DE-NA0003525 with NTESS,
// the U.S. Government retains certain rights in this software.
//
// Part of Kokkos, under the Apache License v2.0 with LLVM Exceptions.
// See https://kokkos.org/LICENSE for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//@HEADER

#include <Kokkos_Core.hpp>

template <class ViewType>
struct ParallelScanFunctor {
  using value_type = double;
  ViewType v;

  explicit ParallelScanFunctor(const ViewType& v_) : v(v_) {}

  KOKKOS_INLINE_FUNCTION
  void operator()(const int idx, value_type& val, const bool& is_final) const {
    // inclusive scan
    val += v(idx);
    if (is_final) {
      v(idx) = val;
    }
  }
};

template <class ScheduleType, class IndexType, class ViewType1, class ViewType2,
          class ViewType3>
void test_policy(int team_range, int thread_range, int vector_range,
                 int outer_repeat, int thread_repeat, int inner_repeat,
                 int team_size, int vector_size, int test_type, ViewType1& v1,
                 ViewType2& v2, ViewType3& v3, double& result,
                 double& result_expect, double& time) {
  using t_policy = Kokkos::TeamPolicy<ScheduleType, IndexType>;
  using t_team   = typename t_policy::member_type;
  Kokkos::Timer timer;

  for (int orep = 0; orep < outer_repeat; orep++) {
    if (test_type == 100) {
      Kokkos::parallel_for(
          "100 outer for", t_policy(team_range, team_size),
          KOKKOS_LAMBDA(const t_team& team) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            v1(idx)  = idx;
            // prevent compiler optimizing loop away
          });
    }

    if (test_type == 110) {
      Kokkos::parallel_for(
          "110 outer for", t_policy(team_range, team_size),
          KOKKOS_LAMBDA(const t_team& team) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            for (int tr = 0; tr < thread_repeat; ++tr) {
              // Each team launches a parallel_for; thread_range is partitioned
              // among team members
              Kokkos::parallel_for(Kokkos::TeamThreadRange(team, thread_range),
                                   [&](const int t) {
                                     v2(idx, t) = t;
                                     // prevent compiler optimizing loop away
                                   });
            }
          });
    }
    if (test_type == 111) {
      Kokkos::parallel_for(
          "111 outer for", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            for (int tr = 0; tr < thread_repeat; ++tr) {
              // Each team launches a parallel_for; thread_range is partitioned
              // among team members
              Kokkos::parallel_for(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t) {
                    for (int vr = 0; vr < inner_repeat; ++vr)
                      Kokkos::parallel_for(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int vi) {
                            v3(idx, t, vi) = vi;
                            // prevent compiler optimizing loop away
                          });
                  });
            }
          });
    }
    if (test_type == 112) {
      Kokkos::parallel_for(
          "112 outer for", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            for (int tr = 0; tr < thread_repeat; ++tr) {
              // Each team launches a parallel_for; thread_range is partitioned
              // among team members
              Kokkos::parallel_for(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t) {
                    double vector_result = 0.0;
                    for (int vr = 0; vr < inner_repeat; ++vr) {
                      vector_result = 0.0;
                      Kokkos::parallel_reduce(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int, double& vval) { vval += 1; },
                          vector_result);
                    }
                    v2(idx, t) = vector_result;
                    // prevent compiler optimizing loop away
                  });
            }
          });
    }
    if (test_type == 120) {
      Kokkos::parallel_for(
          "120 outer for", t_policy(team_range, team_size),
          KOKKOS_LAMBDA(const t_team& team) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            double team_result = 0.0;
            for (int tr = 0; tr < thread_repeat; ++tr) {
              team_result = 0.0;
              Kokkos::parallel_reduce(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int, double& lval) { lval += 1; }, team_result);
            }
            v1(idx) = team_result;
            // prevent compiler optimizing loop away
          });
    }
    if (test_type == 121) {
      Kokkos::parallel_for(
          "121 outer for", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            double team_result = 0.0;
            for (int tr = 0; tr < thread_repeat; ++tr) {
              team_result = 0.0;
              Kokkos::parallel_reduce(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t, double& lval) {
                    lval += 1;
                    for (int vr = 0; vr < inner_repeat; ++vr) {
                      Kokkos::parallel_for(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int vi) {
                            v3(idx, t, vi) = vi;
                            // prevent compiler optimizing loop away
                          });
                    }
                  },
                  team_result);
            }
            v3(idx, 0, 0) = team_result;
            // prevent compiler optimizing loop away
          });
    }
    if (test_type == 122) {
      Kokkos::parallel_for(
          "122 outer for", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            double team_result = 0.0;
            for (int tr = 0; tr < thread_repeat; ++tr) {
              Kokkos::parallel_reduce(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int, double& lval) {
                    double vector_result = 0.0;
                    for (int vr = 0; vr < inner_repeat; ++vr) {
                      vector_result = 0.0;
                      Kokkos::parallel_reduce(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int, double& vval) { vval += 1; },
                          vector_result);
                      lval += vector_result;
                    }
                  },
                  team_result);
            }
            v1(idx) = team_result;
            // prevent compiler optimizing loop away
          });
    }
    if (test_type == 200) {
      Kokkos::parallel_reduce(
          "200 outer reduce", t_policy(team_range, team_size),
          KOKKOS_LAMBDA(const t_team& team, double& lval) {
            lval += team.team_size() * team.league_rank() + team.team_rank();
          },
          result);
      result_expect =
          0.5 * (team_range * team_size) * (team_range * team_size - 1);
      // sum ( seq( [0, team_range*team_size) )
    }
    if (test_type == 210) {
      Kokkos::parallel_reduce(
          "210 outer reduce", t_policy(team_range, team_size),
          KOKKOS_LAMBDA(const t_team& team, double& lval) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            double thread_for = 1.0;
            for (int tr = 0; tr < thread_repeat; tr++) {
              Kokkos::parallel_for(Kokkos::TeamThreadRange(team, thread_range),
                                   [&](const int t) {
                                     v2(idx, t) = t;
                                     // prevent compiler optimizing loop away
                                   });
            }
            lval += (team.team_size() * team.league_rank() + team.team_rank() +
                     thread_for);
          },
          result);
      result_expect =
          0.5 * (team_range * team_size) * (team_range * team_size - 1) +
          (team_range * team_size);
      // sum ( seq( [0, team_range*team_size) + 1 per team_member (total of
      // team_range*team_size) )
    }
    if (test_type == 211) {
      Kokkos::parallel_reduce(
          "211 outer reduce", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team, double& lval) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            double thread_for = 1.0;
            for (int tr = 0; tr < thread_repeat; tr++) {
              Kokkos::parallel_for(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t) {
                    for (int vr = 0; vr < inner_repeat; ++vr)
                      Kokkos::parallel_for(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int vi) {
                            v3(idx, t, vi) = vi;
                            // prevent compiler optimizing loop away
                          });
                  });
            }
            lval += idx + thread_for;
          },
          result);
      result_expect =
          0.5 * (team_range * team_size) * (team_range * team_size - 1) +
          (team_range * team_size);
      // sum ( seq( [0, team_range*team_size) + 1 per team_member (total of
      // team_range*team_size) )
    }
    if (test_type == 212) {
      Kokkos::parallel_reduce(
          "212 outer reduce", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team, double& lval) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            double vector_result = 0.0;
            for (int tr = 0; tr < thread_repeat; tr++) {
              // This parallel_for is executed by each team; the thread_range is
              // partitioned among the team members
              Kokkos::parallel_for(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t) {
                    v2(idx, t) = t;
                    // prevent compiler optimizing loop away
                    for (int vr = 0; vr < inner_repeat; ++vr) {
                      vector_result = 0.0;
                      Kokkos::parallel_reduce(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int vi, double& vval) { vval += vi; },
                          vector_result);
                    }
                  });
            }
            lval += idx + vector_result;
          },
          result);
      result_expect =
          0.5 * (team_range * team_size) * (team_range * team_size - 1) +
          (0.5 * vector_range * (vector_range - 1) * team_range * team_size);
      // sum ( seq( [0, team_range*team_size) + sum( seq( [0, vector_range) )
      // per team_member (total of team_range*team_size) )
    }
    if (test_type == 220) {
      Kokkos::parallel_reduce(
          "220 outer reduce", t_policy(team_range, team_size),
          KOKKOS_LAMBDA(const t_team& team, double& lval) {
            double team_result = 0.0;
            for (int tr = 0; tr < thread_repeat; tr++) {
              Kokkos::parallel_reduce(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t, double& tval) { tval += t; }, team_result);
            }
            lval += team_result * team.league_rank();  // constant * league_rank
          },
          result);
      result_expect = 0.5 * (team_range) * (team_range - 1) * team_size * 0.5 *
                      (thread_range) * (thread_range - 1);
      // sum ( seq( [0, team_range) * constant ); constant = sum( seq( [0,
      // thread_range) )*team_size (1 per member, result for each team)
    }
    if (test_type == 221) {
      Kokkos::parallel_reduce(
          "221 outer reduce", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team, double& lval) {
            long idx = team.league_rank() * team.team_size() + team.team_rank();
            double team_result = 0;
            for (int tr = 0; tr < thread_repeat; tr++) {
              Kokkos::parallel_reduce(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t, double& tval) {
                    double vector_for = 1.0;
                    for (int vr = 0; vr < inner_repeat; ++vr) {
                      Kokkos::parallel_for(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int vi) {
                            v3(idx, t, vi) = vi;
                            // prevent compiler optimizing loop away
                          });
                    }
                    tval += t + vector_for;
                  },
                  team_result);
            }
            lval += team_result * team.league_rank();
          },
          result);
      result_expect =
          0.5 * (team_range) * (team_range - 1) * team_size *
          (0.5 * (thread_range) * (thread_range - 1) + thread_range);
      // sum ( seq( [0, team_range) * constant ) + 1 per member per team;
      // constant = sum( seq( [0, thread_range) )*team_size (1 per member,
      // result for each team)
    }
    if (test_type == 222) {
      Kokkos::parallel_reduce(
          "222 outer reduce", t_policy(team_range, team_size, vector_size),
          KOKKOS_LAMBDA(const t_team& team, double& lval) {
            double team_result = 0.0;
            for (int tr = 0; tr < thread_repeat; tr++) {
              Kokkos::parallel_reduce(
                  Kokkos::TeamThreadRange(team, thread_range),
                  [&](const int t, double& tval) {
                    double vector_result = 0.0;
                    for (int vr = 0; vr < inner_repeat; ++vr) {
                      Kokkos::parallel_reduce(
                          Kokkos::ThreadVectorRange(team, vector_range),
                          [&](const int vi, double& vval) { vval += vi; },
                          vector_result);
                    }
                    tval += t + vector_result;
                  },
                  team_result);
            }
            lval += team_result * team.league_rank();
          },
          result);
      result_expect =
          0.5 * (team_range) * (team_range - 1) * team_size *
          (0.5 * (thread_range) * (thread_range - 1) +
           thread_range * 0.5 * (vector_range) * (vector_range - 1));
      // sum ( seq( [0, team_range) * constant ) + 1 + sum( seq([0,vector_range)
      // ) per member per team; constant = sum( seq( [0, thread_range)
      // )*team_size (1 per member, result for each team)
    }

    // parallel_for RangePolicy: range = team_size*team_range
    if (test_type == 300) {
      Kokkos::parallel_for(
          "300 outer for", static_cast<size_t>(team_size) * team_range,
          KOKKOS_LAMBDA(const int idx) {
            v1(idx) = idx;
            // prevent compiler from optimizing away the loop
          });
    }
    // parallel_reduce RangePolicy: range = team_size*team_range
    if (test_type == 400) {
      Kokkos::parallel_reduce(
          "400 outer reduce", static_cast<size_t>(team_size) * team_range,
          KOKKOS_LAMBDA(const int idx, double& val) { val += idx; }, result);
      result_expect =
          0.5 * (team_size * team_range) * (team_size * team_range - 1);
    }
    // parallel_scan RangePolicy: range = team_size*team_range
    if (test_type == 500) {
      Kokkos::parallel_scan("500 outer scan",
                            static_cast<size_t>(team_size) * team_range,
                            ParallelScanFunctor<ViewType1>(v1)
#if 0
        // This does not compile with pre Cuda 8.0 - see Github Issue #913 for explanation
        KOKKOS_LAMBDA (const int idx, double& val, const bool& final) {
          // inclusive scan
          val += v1(idx);
          if ( final ) {
            v1(idx) = val;
          }
        }
#endif
      );
      // result = v1( team_size*team_range - 1 ); // won't work with Cuda - need
      // to copy result back to host to print result_expect =
      // 0.5*(team_size*team_range)*(team_size*team_range-1);
    }

  }  // end outer for loop

  time = timer.seconds();
}  // end test_policy
